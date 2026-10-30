import requests
import random
import os
import urllib3
import base64
import hashlib
import json
import time
import logging
import threading
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import BoundedSemaphore

# 禁用 SSL 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("EmbyClient")

class EmbyClient:
    """
    Emby API 客户端 (V6.3 - 优化版)
    修改记录:
    1. get_libraries 增加返回物理路径 (Locations)，用于 Webhook 路径匹配。
    """
    def __init__(self, host, key, public_host=None, user_name=None):
        self.host = host.rstrip('/')
        self.public_host = public_host.rstrip('/') if public_host else self.host
        self.key = key
        self.user_name = str(user_name or '').strip()
        self.user_id = None
        
        # --- 连接池 (仅用于查询元数据，不限制上传速度) ---
        self.session = requests.Session()
        
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST", "PUT", "DELETE", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retries, pool_connections=50, pool_maxsize=50)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.headers.update({
            "X-Emby-Token": key, 
            "User-Agent": "PosterMaker/Web/6.0"
        })
        
        # 强制直连配置
        self.proxies = { "http": None, "https": None }
        self.timeout = 30

        # 并发控制 (仅限制查询，不限制上传)
        self.semaphore = BoundedSemaphore(20)
        self.cover_verify_delays = [0.25, 0.75]

    def close(self):
        """关闭连接池"""
        try:
            self.session.close()
        except:
            pass

    def get_image_data(self, image_url):
        """Download an Emby image with the configured API credentials."""
        if not image_url:
            return None, None
        try:
            response = self.session.get(
                image_url,
                timeout=self.timeout,
                verify=False,
                proxies=self.proxies,
            )
            response.raise_for_status()
            content_type = (response.headers.get("Content-Type") or "image/jpeg").split(";", 1)[0]
            if not response.content or not content_type.startswith("image/"):
                return None, None
            return response.content, content_type
        except Exception as exc:
            logger.warning(f"下载 Emby 通知海报失败: {exc}")
            return None, None

    def _request(self, method, endpoint, **kwargs):
        """统一请求封装 (仅用于查询)"""
        if endpoint.startswith("http"):
            url = endpoint
        else:
            url = f"{self.host}/{endpoint.lstrip('/')}"

        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', False)
        kwargs.setdefault('proxies', self.proxies)

        with self.semaphore:
            try:
                resp = self.session.request(method, url, **kwargs)
                resp.raise_for_status()
                try:
                    return resp.json()
                except:
                    return resp
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    # 404不打印error，保持日志干净
                    pass
                else:
                    logger.error(f"HTTP 请求失败 ({e.response.status_code}): {url} | {e}")
                raise
            except Exception as e:
                logger.error(f"请求异常: {e} | URL: {url}")
                raise

    def _get_user_id(self):
        if self.user_id:
            return self.user_id
        try:
            res = self._request("GET", "emby/Users")
            if self.user_name:
                for user in res:
                    if str(user.get('Name') or '').strip() == self.user_name:
                        self.user_id = user['Id']
                        return self.user_id
                raise ValueError(f"未找到 Emby 用户: {self.user_name}")
            for user in res:
                if user.get('Policy', {}).get('IsAdministrator', False):
                    self.user_id = user['Id']
                    return self.user_id
        except ValueError:
            raise
        except Exception as exc:
            if self.user_name:
                raise ValueError(f"无法读取 Emby 用户: {self.user_name}") from exc
        return None

    # =========================================================================
    # ★★★ 核心加速区：上传逻辑 ★★★
    # =========================================================================

    def _get_boxset_map(self):
        """[复刻] 获取合集映射"""
        uid = self._get_user_id()
        mapping = {}
        try:
            params = {
                "Recursive": "true",
                "IncludeItemTypes": "BoxSet,Folder",
                "Fields": "ParentId"
            }
            # 使用 session 查询以减轻服务器握手压力
            endpoint = f"emby/Users/{uid}/Items" if uid else "emby/Items"
            res = self._request("GET", endpoint, params=params)
            
            items = res.get('Items', []) if isinstance(res, dict) else []
            for item in items:
                mapping[item['Name']] = item['Id']
        except: 
            pass
        return mapping

    def _resolve_real_id(self, item_id):
        """[复刻] 反查真实ID"""
        uid = self._get_user_id()
        try:
            endpoint = f"emby/Users/{uid}/Items/{item_id}" if uid else f"emby/Items/{item_id}"
            info = self._request("GET", endpoint)
            
            name = info.get('Name')
            if not name: return None
            
            boxset_map = self._get_boxset_map()
            return boxset_map.get(name)
        except: 
            return None

    def _detect_image_mime(self, image_data):
        mime_type = "image/jpeg"
        if image_data.startswith(b'\x89PNG'): mime_type = "image/png"
        elif image_data.startswith(b'GIF'): mime_type = "image/gif"
        return mime_type

    def _image_hash(self, image_data):
        if not image_data:
            return None
        return hashlib.sha256(image_data).hexdigest()

    def _primary_cover_url(self, target_id):
        return f"{self.host}/emby/Items/{target_id}/Images/Primary"

    def _primary_cover_headers(self, image_data=None):
        headers = {
            "X-Emby-Token": self.key,
            "User-Agent": "PosterMaker/Web/6.0",
            "Accept": "application/json"
        }
        if image_data is not None:
            headers["Content-Type"] = self._detect_image_mime(image_data)
        return headers

    def _download_primary_cover_direct(self, target_id, tag=None):
        params = {
            "quality": 100,
            "v": str(int(time.time() * 1000))
        }
        if tag:
            params["tag"] = tag
        try:
            res = requests.get(
                self._primary_cover_url(target_id),
                headers=self._primary_cover_headers(),
                params=params,
                verify=False,
                proxies=self.proxies,
                timeout=self.timeout
            )
            if res.status_code == 200 and res.content:
                return res.content
        except Exception as e:
            logger.debug(f"读取 Primary 图片失败: item_id={target_id}, error={e}")
        return None

    def _get_primary_image_tag(self, target_id):
        endpoints = []
        uid = self._get_user_id()
        if uid:
            endpoints.append(f"emby/Users/{uid}/Items/{target_id}")
        endpoints.append(f"emby/Items/{target_id}")

        for endpoint in endpoints:
            try:
                info = self._request("GET", endpoint, params={"Fields": "ImageTags"})
                tag = (info.get("ImageTags") or {}).get("Primary")
                if tag:
                    return tag
            except Exception as e:
                logger.debug(f"读取 Primary ImageTag 失败: item_id={target_id}, endpoint={endpoint}, error={e}")
        return None

    def _get_primary_cover_state(self, target_id, include_data=False):
        tag = self._get_primary_image_tag(target_id)
        data = self._download_primary_cover_direct(target_id, tag=tag) if include_data else None
        state = {
            "tag": tag,
            "hash": self._image_hash(data),
            "has_image": bool(tag or data)
        }
        if include_data:
            state["data"] = data
        return state

    def _cover_changed(self, before_state, after_state, upload_hash):
        before_tag = before_state.get("tag")
        after_tag = after_state.get("tag")
        before_hash = before_state.get("hash")
        after_hash = after_state.get("hash")

        if before_tag and after_tag and before_tag != after_tag:
            return True
        if before_hash and after_hash and before_hash != after_hash:
            return True
        if not before_tag and not before_hash and (after_tag or after_hash):
            return True
        if upload_hash and after_hash and upload_hash == after_hash:
            return True
        return False

    def _wait_for_cover_change(self, target_id, before_state, image_data):
        upload_hash = self._image_hash(image_data)
        for index, delay in enumerate([0] + self.cover_verify_delays):
            if index > 0 and delay > 0:
                time.sleep(delay)
            after_state = self._get_primary_cover_state(target_id)
            if self._cover_changed(before_state, after_state, upload_hash):
                return True
        return False

    def _post_primary_cover(self, target_id, image_data, encode_base64=False):
        try:
            payload = base64.b64encode(image_data) if encode_base64 else image_data
            res = requests.post(
                self._primary_cover_url(target_id),
                headers=self._primary_cover_headers(image_data),
                data=payload,
                verify=False,
                proxies=self.proxies,
                timeout=self.timeout
            )
            return res.status_code in [200, 204]
        except Exception as e:
            logger.debug(f"上传 Primary 图片失败: item_id={target_id}, base64={encode_base64}, error={e}")
        return False

    def _upload_cover_to_target(self, target_id, image_data):
        before_state = self._get_primary_cover_state(target_id)

        # StrmAssistant 的通知系统增强开启时，Emby 对媒体库封面二进制上传会返回 204，
        # 但 Primary 图片不会变化；base64 上传可以正常落地，所以这里优先使用 base64。
        for encode_base64 in (True, False):
            if not self._post_primary_cover(target_id, image_data, encode_base64=encode_base64):
                continue
            if self._wait_for_cover_change(target_id, before_state, image_data):
                return True
            logger.warning(f"封面上传返回成功但 Emby 图片未变化: item_id={target_id}, base64={encode_base64}")

        return False

    def upload_cover(self, item_id, image_data):
        """
        上传封面并确认 Emby Primary 图片实际变化。
        """
        if self._upload_cover_to_target(item_id, image_data):
            return True

        real_id = self._resolve_real_id(item_id)
        if real_id and str(real_id) != str(item_id):
            return self._upload_cover_to_target(real_id, image_data)

        return False

    # =========================================================================
    # ★★★ 其他功能 (保持不变) ★★★
    # =========================================================================

    def download_cover(self, item_id):
        try:
            # 下载也建议用 requests 直连，避免抢占查询通道
            url = f"{self.host}/emby/Items/{item_id}/Images/Primary"
            res = requests.get(url, headers={"X-Emby-Token": self.key}, verify=False, proxies=self.proxies, timeout=self.timeout)
            if res.status_code == 200: return res.content
        except: pass
        
        try:
            info = self._request("GET", f"emby/Items/{item_id}")
            if "Primary" in info.get("ImageTags", {}):
                tag = info["ImageTags"]["Primary"]
                url = f"{self.host}/emby/Items/{item_id}/Images/Primary?tag={tag}"
                res = requests.get(url, headers={"X-Emby-Token": self.key}, verify=False, proxies=self.proxies, timeout=self.timeout)
                if res.status_code == 200: return res.content
        except: pass

        real_id = self._resolve_real_id(item_id)
        if real_id and str(real_id) != str(item_id):
            return self.download_cover(real_id)
        return None

    def check_connection(self):
        try:
            # ALSemby 只需要验证媒体库读取能力。System/Info 可能要求更高权限，
            # 不能作为封面生成/真实库工作流的连接成功判据。
            self._request("GET", "emby/Library/VirtualFolders", timeout=5)
            return {"ok": True}
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response is not None else None
            if status_code == 401:
                message = "Emby 拒绝读取媒体库，请检查 API Key 是否有媒体库读取权限"
            elif status_code == 403:
                message = "Emby API Key 权限不足，无法读取媒体库"
            elif status_code:
                message = f"Emby 连接失败，HTTP 状态码 {status_code}"
            else:
                message = "Emby 连接失败，未返回有效状态码"
            return {"ok": False, "status_code": status_code, "message": message}
        except requests.exceptions.RequestException as e:
            return {"ok": False, "status_code": None, "message": f"无法连接 Emby: {e}"}
        except Exception as e:
            return {"ok": False, "status_code": None, "message": f"Emby 检查失败: {e}"}

    def test_connection(self):
        return self.check_connection().get("ok", False)

    def get_libraries(self):
            """
            [优化版] 优先使用 Users/Views 获取用户设置的正确排序，
            同时合并 VirtualFolders 的物理路径信息 (Locations)。
            """
            # 1. 先获取物理路径映射 (来自 VirtualFolders 接口)
            # 目的：为了拿到 paths 用于 Webhook/RSS 匹配，因为 Views 接口不带路径信息
            paths_map = {}
            vf_items = []
            try:
                res = self._request("GET", "emby/Library/VirtualFolders")
                if isinstance(res, list):
                    vf_items = res
                    for item in res:
                        # VirtualFolders 返回的是 ItemId，提取 Locations
                        paths_map[item.get('ItemId')] = item.get('Locations', [])
            except Exception as e:
                logger.warning(f"获取 VirtualFolders 失败 (不影响显示，仅影响路径匹配): {e}")

            # 2. 获取用户视图 (Views) - 这才是 Emby 界面显示的正确顺序
            uid = self._get_user_id()
            if uid:
                try:
                    res = self._request("GET", f"emby/Users/{uid}/Views")
                    items = res.get('Items', []) if isinstance(res, dict) else res
                    
                    final_libs = []
                    for item in items:
                        # 这里可以过滤掉不需要显示的类型，比如 'boxsets' (合集)
                        # if item.get('CollectionType') == 'boxsets': continue 

                        lib_id = item.get('Id')
                        
                        # ★★★ 关键点：尝试匹配物理路径 ★★★
                        # Views 里的 Id 对应 VirtualFolders 里的 ItemId
                        # 如果匹配到了，就用 VirtualFolders 里的路径；没匹配到就为空
                        locations = paths_map.get(lib_id, [])

                        final_libs.append({
                            "name": item.get('Name'),
                            "id": lib_id,
                            "type": item.get('CollectionType', 'unknown'),
                            "paths": locations
                        })
                    
                    # 如果成功获取并整合了数据，直接返回这个有序列表
                    if final_libs or self.user_name:
                        return final_libs

                except Exception as e:
                    logger.error(f"获取用户视图排序失败: {e}")
                    if self.user_name:
                        raise

            # 3. 兜底方案：如果上面的 Views 获取失败，退回到使用 VirtualFolders
            # 虽然顺序可能是乱的（字母序），但至少能显示出来，不至于列表为空
            if vf_items:
                return [{
                    "name": item['Name'], 
                    "id": item['ItemId'], 
                    "type": item.get('CollectionType', 'unknown'), 
                    "paths": item.get('Locations', [])
                } for item in vf_items]
            
            return []

    def get_libraries_with_covers(self):
        try:
            libs = self.get_libraries()
            result = []
            for lib in libs:
                i_id = lib['id']
                img_url = f"{self.public_host}/emby/Items/{i_id}/Images/Primary?maxHeight=300&quality=90"
                result.append({"name": lib['name'], "id": i_id, "cover_url": img_url, "type": lib['type']})
            return result
        except ValueError:
            raise
        except Exception:
            return []

    def get_assets(
        self,
        library_id,
        mode="random",
        poster_limit=6,
        backdrop_limit=1,
        fallback_to_next_backdrop=True,
    ):
        bg_url = None
        backdrops = [] 
        posters = []
        poster_backdrops = []
        sequential_pairs = []
        count = self.get_library_count(library_id)
        
        uid = self._get_user_id()
        endpoint = f"emby/Users/{uid}/Items" if uid else "emby/Items"

        def sort_release_items(items):
            """Keep release-date mode deterministic when dates are incomplete."""
            if mode != "premiere":
                return items

            def release_key(item):
                # Emby normally orders by PremiereDate. ProductionYear keeps
                # older/incomplete metadata useful; DateCreated breaks ties.
                premiere_date = item.get("PremiereDate") or ""
                production_year = str(item.get("ProductionYear") or "").zfill(4)
                created_date = item.get("DateCreated") or ""
                effective_date = premiere_date or (f"{production_year}-01-01" if production_year.strip("0") else created_date)
                return (effective_date, created_date)

            return sorted(items, key=release_key, reverse=True)

        def apply_asset_sort(params, include_sort_name=False):
            if mode == "random":
                params["SortBy"] = "Random"
            elif mode == "premiere":
                # PremiereDate is the release date exposed by Emby.
                params["SortBy"] = "PremiereDate"
                params["SortOrder"] = "Descending"
            else:
                params["SortBy"] = "DateCreated,SortName" if include_sort_name else "DateCreated"
                params["SortOrder"] = "Descending"

        if backdrop_limit > 0:
            page_limit = max(50, min(200, poster_limit * 10, max(50, count)))
            params = {
                "ParentId": library_id, 
                "Recursive": "true", 
                "IncludeItemTypes": "Movie,Series", 
                "ImageTypes": "Backdrop", 
                "EnableImageTypes": "Primary,Backdrop,Logo",
                "Fields": "ImageTags,BackdropImageTags,PremiereDate,ProductionYear,DateCreated", 
                "Limit": page_limit,
            }
            apply_asset_sort(params, include_sort_name=True)

            try:
                valid_items = []
                start_index = 0
                seen_item_ids = set()
                while True:
                    params["StartIndex"] = start_index
                    res = self._request("GET", endpoint, params=params)
                    items = sort_release_items(res.get('Items', []))
                    new_item_count = 0
                    for item in items:
                        item_id = item.get('Id')
                        if not item_id or item_id in seen_item_ids:
                            continue
                        seen_item_ids.add(item_id)
                        new_item_count += 1
                        if mode != "random" and fallback_to_next_backdrop:
                            # A sequential dynamic entry is usable only when
                            # its poster and own backdrop are both available.
                            if 'Primary' not in item.get('ImageTags', {}):
                                continue
                        url = None
                        if 'BackdropImageTags' in item and len(item['BackdropImageTags']) > 0:
                            tag = item['BackdropImageTags'][0]
                            url = f"{self.host}/emby/Items/{item_id}/Images/Backdrop/0?MaxHeight=2160&tag={tag}&quality=90"
                        elif 'Backdrop' in item.get('ImageTags', {}):
                            tag = item['ImageTags']['Backdrop']
                            url = f"{self.host}/emby/Items/{item_id}/Images/Backdrop/0?MaxHeight=2160&tag={tag}&quality=90"
                        if url:
                            valid_items.append(url)
                            primary_tag = item.get('ImageTags', {}).get('Primary')
                            if primary_tag:
                                poster_url = f"{self.host}/emby/Items/{item_id}/Images/Primary?MaxHeight=600&tag={primary_tag}"
                                sequential_pairs.append((poster_url, url))

                    should_fill_pairs = mode != "random" and fallback_to_next_backdrop and poster_limit > 0
                    if not should_fill_pairs or len(sequential_pairs) >= poster_limit:
                        break
                    if not items or new_item_count == 0:
                        break

                    next_index = start_index + len(items)
                    total_records = res.get('TotalRecordCount')
                    if total_records is not None:
                        if next_index >= int(total_records):
                            break
                    elif len(items) < page_limit:
                        break
                    start_index = next_index

                if len(valid_items) > 0:
                    if mode == "random" and len(valid_items) > backdrop_limit:
                        backdrops = random.sample(valid_items, backdrop_limit)
                    else:
                        backdrops = valid_items[:backdrop_limit]
                    bg_url = backdrops[0] 
            except Exception as e: 
                logger.error(f"Error fetching backdrops: {e}")

        if poster_limit > 0:
            p_params = {
                "ParentId": library_id, 
                "Recursive": "true", 
                "IncludeItemTypes": "Movie,Series", 
                "ImageTypes": "Primary", 
                "Fields": "ImageTags,BackdropImageTags,PremiereDate,ProductionYear,DateCreated", 
                "Limit": max(30, poster_limit + 10) 
            }
            apply_asset_sort(p_params)
            
            try:
                res = self._request("GET", endpoint, params=p_params)
                p_items = sort_release_items(res.get('Items', []))
                valid_posters = []
                for item in p_items:
                    if 'Primary' in item.get('ImageTags', {}):
                        p_tag = item['ImageTags'].get('Primary')
                        poster_url = f"{self.host}/emby/Items/{item['Id']}/Images/Primary?MaxHeight=600&tag={p_tag}"
                        backdrop_url = None
                        backdrop_tags = item.get('BackdropImageTags') or []
                        if backdrop_tags:
                            backdrop_url = f"{self.host}/emby/Items/{item['Id']}/Images/Backdrop/0?MaxHeight=2160&tag={backdrop_tags[0]}&quality=90"
                        elif item.get('ImageTags', {}).get('Backdrop'):
                            backdrop_tag = item['ImageTags']['Backdrop']
                            backdrop_url = f"{self.host}/emby/Items/{item['Id']}/Images/Backdrop/0?MaxHeight=2160&tag={backdrop_tag}&quality=90"
                        valid_posters.append((poster_url, backdrop_url))
                if len(valid_posters) > 0:
                    paired_random = (
                        [pair for pair in valid_posters if pair[1]]
                        if mode == "random" and backdrop_limit >= poster_limit > 0
                        else valid_posters
                    )
                    random_pool = paired_random or valid_posters
                    if mode == "random" and len(random_pool) > poster_limit:
                        selected_posters = random.sample(random_pool, poster_limit)
                    elif mode == "random":
                        selected_posters = random_pool[:poster_limit]
                    elif mode != "random" and fallback_to_next_backdrop and sequential_pairs:
                        # Skip the whole item when its backdrop is missing so
                        # poster N always uses backdrop N from the same title.
                        selected_posters = sequential_pairs[:poster_limit]
                    else:
                        selected_posters = valid_posters[:poster_limit]
                    posters = [poster for poster, _ in selected_posters]
                    poster_backdrops = [backdrop for _, backdrop in selected_posters]

                    if mode != "random" and not fallback_to_next_backdrop and backdrop_limit > 0:
                        # Strict mode keeps the newest poster and only accepts
                        # that same item's backdrop. Missing means the engine's
                        # default background is used.
                        newest_backdrop = valid_posters[0][1]
                        backdrops = [newest_backdrop] if newest_backdrop else []
                        bg_url = newest_backdrop
            except Exception as e: 
                logger.error(f"Error fetching posters: {e}")

        return {
            "bg_url": bg_url,
            "backdrops": backdrops,
            "posters": posters,
            "poster_backdrops": poster_backdrops,
            "count": count,
        }

    def get_item_images(self, item_id, img_type='Backdrop'):
        images = []
        try:
            uid = self._get_user_id()
            endpoint = f"emby/Users/{uid}/Items/{item_id}" if uid else f"emby/Items/{item_id}"
            
            info = self._request("GET", endpoint)
            
            if img_type == 'Backdrop':
                tags = info.get('BackdropImageTags', [])
                for i, tag in enumerate(tags):
                    url = f"{self.public_host}/emby/Items/{item_id}/Images/Backdrop/0?tag={tag}&quality=90&maxHeight=1080"
                    images.append(url)
            elif img_type == 'Primary':
                if 'Primary' in info.get('ImageTags', {}):
                    tag = info['ImageTags']['Primary']
                    url = f"{self.public_host}/emby/Items/{item_id}/Images/Primary?tag={tag}&quality=90&maxHeight=600"
                    images.append(url)
        except: 
            pass
        return images

    def get_random_pool(self, library_id, img_type='Backdrop', limit=50):
        uid = self._get_user_id()
        params = {
            "ParentId": library_id, 
            "Recursive": "true", 
            "IncludeItemTypes": "Movie,Series",
            "SortBy": "Random", 
            "Limit": limit, 
            "Fields": "ImageTags,BackdropImageTags", 
            "ImageTypes": img_type
        }
        urls = []
        try:
            endpoint = f"emby/Users/{uid}/Items" if uid else "emby/Items"
            res = self._request("GET", endpoint, params=params)
            items = res.get('Items', [])
            
            for item in items:
                i_id = item['Id']
                if img_type == 'Backdrop':
                    if item.get('BackdropImageTags'):
                        tag = item['BackdropImageTags'][0]
                        urls.append(f"{self.public_host}/emby/Items/{i_id}/Images/Backdrop/0?tag={tag}&maxHeight=1080&quality=90")
                else: 
                    if 'Primary' in item.get('ImageTags', {}):
                        tag = item['ImageTags']['Primary']
                        urls.append(f"{self.public_host}/emby/Items/{i_id}/Images/Primary?tag={tag}&maxHeight=600&quality=90")
        except: 
            pass
        return urls
    
    def search_items(self, query, library_id=None, img_type="Primary"):
        uid = self._get_user_id()
        params = {
            "SearchTerm": query, 
            "Recursive": "true", 
            "IncludeItemTypes": "Movie,Series,BoxSet", 
            "Limit": 20,
            "Fields": "ImageTags,BackdropImageTags,PrimaryImageAspectRatio"
        }
        if library_id: 
            params["ParentId"] = library_id
            
        results = []
        try:
            endpoint = f"emby/Users/{uid}/Items" if uid else "emby/Items"
            res = self._request("GET", endpoint, params=params)
            items = res.get('Items', [])
            
            for i in items:
                img_url = None
                if img_type == 'Backdrop' and i.get('BackdropImageTags'):
                    tag = i['BackdropImageTags'][0]
                    img_url = f"{self.public_host}/emby/Items/{i['Id']}/Images/Backdrop/0?tag={tag}&maxHeight=400&maxWidth=711&quality=90"
                elif 'Primary' in i.get('ImageTags', {}):
                    tag = i['ImageTags']['Primary']
                    img_url = f"{self.public_host}/emby/Items/{i['Id']}/Images/Primary?tag={tag}&maxHeight=400&quality=90"
                
                results.append({
                    "name": i.get('Name'), 
                    "id": i.get('Id'), 
                    "type": i.get('Type'), 
                    "year": i.get('ProductionYear'), 
                    "image": img_url 
                })
        except: 
            pass
        return results

    def find_path_by_id(self, tmdb_id, item_type='Movie', exclude_path=None):
        """
        根据 TMDb ID 查找物理路径 (支持版本合并/MediaSources挖掘)
        """
        if not tmdb_id: return None
        
        search_type = 'Series' if item_type == 'Series' else 'Movie'

        params = {
            "Recursive": "true",
            "AnyProviderIdEquals": f"Tmdb.{tmdb_id}",
            "IncludeItemTypes": search_type,
            # 【关键修改 1】增加 MediaSources 字段，防止 Emby 合并版本导致找不到源路径
            "Fields": "Path,MediaSources",
        }
        
        try:
            endpoint = "emby/Items"
            user_id = self._get_user_id()
            if user_id: params['UserId'] = user_id

            res = self._request("GET", endpoint, params=params)
            
            if res.get("Items"):
                for item in res["Items"]:
                    found_type = item.get("Type")
                    if found_type != search_type: continue

                    # --- 内部函数：检查路径是否有效 ---
                    def is_valid_source(p):
                        if not p: return False
                        if not exclude_path: return True
                        # 路径标准化对比
                        p_check = p.replace('\\', '/').rstrip('/')
                        p_exclude = exclude_path.replace('\\', '/').rstrip('/')
                        return not p_check.startswith(p_exclude)

                    # 1. 先检查顶层 Path
                    main_path = item.get("Path")
                    if is_valid_source(main_path):
                        return main_path

                    # 2. 【核心修复】如果顶层 Path 被排除，检查 MediaSources (应对版本合并)
                    if item.get("MediaSources"):
                        for source in item["MediaSources"]:
                            sub_path = source.get("Path")
                            if is_valid_source(sub_path):
                                logger.info(f"  [DeepSearch] 在合并版本中找到了源路径: {sub_path}")
                                return sub_path
                
        except Exception as e: 
            logger.error(f"ID寻址失败 ({tmdb_id}): {e}")
        return None

    def get_series_episode_counts(self, tmdb_id: int) -> dict:
        """
        返回 {season_number: {episode_numbers}} 表示 Emby 中该系列拥有的所有集。
        系列不在 Emby 则返回空 dict。
        """
        if not tmdb_id:
            return {}
        try:
            # 1. 查找 Emby 中的 Series ID
            params = {
                "Recursive": "true",
                "AnyProviderIdEquals": f"Tmdb.{tmdb_id}",
                "IncludeItemTypes": "Series",
                "Fields": "Id",
            }
            user_id = self._get_user_id()
            if user_id:
                params["UserId"] = user_id
            res = self._request("GET", "emby/Items", params=params)
            items = res.get("Items", [])
            if not items:
                return {}
            series_id = items[0].get("Id")
            if not series_id:
                return {}

            # 2. 先获取该剧的所有季
            season_params = {
                "ParentId": series_id,
                "IncludeItemTypes": "Season",
                "Fields": "Id,IndexNumber",
            }
            season_endpoint = f"emby/Users/{user_id}/Items" if user_id else "emby/Items"
            season_res = self._request("GET", season_endpoint, params=season_params)

            # 3. 逐季获取集数
            result = {}
            for season_item in season_res.get("Items", []):
                season_num = season_item.get("IndexNumber")
                season_id = season_item.get("Id")
                if season_num is None or not season_id:
                    continue
                ep_params = {
                    "ParentId": season_id,
                    "IncludeItemTypes": "Episode",
                    "Fields": "IndexNumber",
                    "Limit": 10000,
                }
                ep_res = self._request("GET", season_endpoint, params=ep_params)
                for ep in ep_res.get("Items", []):
                    ep_num = ep.get("IndexNumber")
                    if ep_num is not None:
                        result.setdefault(season_num, set()).add(ep_num)

            logger.info(f"[get_series_episode_counts] TMDB:{tmdb_id} Series:{series_id} 结果: { {k: len(v) for k, v in result.items()} }")
            return result
        except Exception as e:
            logger.warning(f"获取剧集集数失败 ({tmdb_id}): {e}")
            return {}

    def ensure_library_exists(self, name, path, collection_type="movies"):
        """
        [核心修复] 自动建库逻辑 - 增加路径存在性检查，防止 500 错误
        """
        existing_libs = self.get_libraries()
        target_lib = next((lib for lib in existing_libs if lib['name'] == name), None)

        if target_lib:
            # ★★★ 新增逻辑：检查路径是否已存在 ★★★
            try:
                # 获取库的详细信息（包含 LibraryOptions 和 PathInfos）
                res = self._request("GET", "emby/Library/VirtualFolders")
                
                # 在结果中找到目标库
                remote_lib = next((l for l in res if l['Name'] == name), None)
                
                if remote_lib:
                    # 检查路径是否已在 Locations 中
                    locations = remote_lib.get('Locations', [])
                    # 简单规范化路径对比 (去除末尾斜杠)
                    norm_path = path.rstrip('/\\')
                    norm_locations = [l.rstrip('/\\') for l in locations]
                    
                    if norm_path in norm_locations:
                        logger.info(f"媒体库 '{name}' 已包含路径 '{path}'，跳过添加。")
                        return target_lib['id']
            except Exception as e:
                logger.warning(f"检查库路径失败，将尝试直接添加: {e}")

            try:
                params = { "Name": name, "Path": path, "Refresh": "true" }
                self._request("POST", "emby/Library/VirtualFolders/Paths", params=params)
            except: pass
            return target_lib['id']

        logger.info(f"正在创建新库 (Strict Mode): {name} -> {path}")
        
        no_scrape_options = {
            "EnableArchiveMediaFiles": False,
            "EnablePhotos": False,
            "EnableRealtimeMonitor": True,  
            "ExtractChapterImagesDuringLibraryScan": False, 
            "DownloadImagesInAdvance": False,
            "SaveLocalMetadata": False, 
            "EnableInternetProviders": False,
            "TypeOptions": [
                {"Type": "Movie", "MetadataFetchers": [], "ImageFetchers": [], "ImageOptions": []},
                {"Type": "Series", "MetadataFetchers": [], "ImageFetchers": [], "ImageOptions": []},
                {"Type": "Season", "MetadataFetchers": [], "ImageFetchers": []},
                {"Type": "Episode", "MetadataFetchers": [], "ImageFetchers": []}
            ]
        }

        try:
            params = {
                "Name": name,
                "CollectionType": collection_type,
                "RefreshKey": f"AutoCreated_{int(time.time())}"
            }
            
            body = {
                "LibraryOptions": no_scrape_options
            }
            body["LibraryOptions"]["PathInfos"] = [{"Path": path}]

            self._request("POST", "emby/Library/VirtualFolders", params=params, json=body)
            logger.info(f"Successfully created library: {name}")
            
            time.sleep(2)
            new_libs = self.get_libraries()
            new_target = next((lib for lib in new_libs if lib['name'] == name), None)
            if new_target: return new_target['id']
        except Exception as e:
            logger.error(f"Create library failed: {e}")
        return None
    
    def delete_library(self, library_id):
        """
        [强制修改] 按照指令：直接发送库 ID 来删除
        请求 URL 将变为：DELETE /emby/Library/VirtualFolders?id=xxxx&Refresh=false
        """
        if not library_id: return False
        
        try:
            logger.info(f"正在通过 ID 删除媒体库: {library_id}")
            
            # ★★★ 严格按照你的要求修改 ★★★
            # 1. 参数改为 id (而不是 Name)
            # 2. Refresh=false 用于解决 500 超时报错
            params = { 
                "id": library_id, 
                "Refresh": "false" 
            }
            
            # 直接向 VirtualFolders 接口发送带 id 的 DELETE 请求
            self._request("DELETE", "emby/Library/VirtualFolders", params=params)
            
            logger.info(f"媒体库删除指令已发送 (ID: {library_id})")
            return True

        except Exception as e:
            logger.error(f"通过 ID 删除请求遇到错误: {e}")
            
            # 为了确保一定能删掉，如果上面的报错，尝试通用的 Item 删除接口 (这也是一种通过 ID 删库的方式)
            try:
                logger.info("尝试使用 Item 接口强制删除...")
                self._request("DELETE", f"emby/Items/{library_id}")
                return True
            except:
                return False

    def delete_library_by_path(self, path):
            """
            [纯路径模式] 仅根据物理路径查找并删除媒体库
            :param path: 库在硬盘上的绝对路径
            """
            if not path:
                logger.warning("未提供路径，无法执行删除操作")
                return False

            # 1. 路径标准化函数 (处理斜杠和大小写，确保匹配准确)
            def normalize(p):
                return p.replace('\\', '/').rstrip('/').lower()

            target_path = normalize(path)
            all_libs = self.get_libraries()
            target_lib = None

            # 2. 遍历查找匹配路径的库
            for lib in all_libs:
                # lib['paths'] 来自 get_libraries 中的 Locations 字段
                if 'paths' in lib and lib['paths']:
                    for loc in lib['paths']:
                        if normalize(loc) == target_path:
                            target_lib = lib
                            logger.info(f"路径匹配成功! 路径: '{path}' -> 对应库名: '{lib['name']}'")
                            break
                if target_lib:
                    break
            
            if not target_lib:
                logger.warning(f"Emby 中未找到路径为 '{path}' 的媒体库，跳过删除。")
                return True # 找不到视为已清理，返回 True

            # 3. 使用找到的真实名称执行删除
            real_name = target_lib['name']
            try:
                logger.info(f"正在请求删除 Emby 媒体库: {real_name}")
                # Emby 删除接口主要依赖 Name 参数
                params = {
                    "Name": real_name, 
                    "Refresh": "true"
                }
                self._request("DELETE", "emby/Library/VirtualFolders", params=params)
                return True
            except Exception as e:
                logger.error(f"删除媒体库失败: {real_name} | {e}")
                return False

    def get_library_count(self, library_id):
        uid = self._get_user_id()
        try:
            params = { "ParentId": library_id, "Recursive": "true", "IncludeItemTypes": "Movie,Series", "Limit": 0 }
            endpoint = f"emby/Users/{uid}/Items" if uid else "emby/Items"
            res = self._request("GET", endpoint, params=params)
            return res.get('TotalRecordCount', 0)
        except ValueError:
            raise
        except Exception:
            return 0

    def get_all_library_items(self, item_types="Movie,Series"):
        """全量扫描媒体库，返回 { "tmdb_id:type": True } dict"""
        uid = self._get_user_id()
        endpoint = f"emby/Users/{uid}/Items" if uid else "emby/Items"
        results = {}
        start = 0
        limit = 200
        while True:
            params = {
                "Recursive": "true",
                "IncludeItemTypes": item_types,
                "Fields": "ProviderIds",
                "StartIndex": start,
                "Limit": limit,
            }
            try:
                data = self._request("GET", endpoint, params=params)
            except Exception as e:
                logger.error(f"扫描媒体库失败 (StartIndex={start}): {e}")
                break
            items = data.get("Items", [])
            if not items:
                break
            for item in items:
                provider_ids = item.get("ProviderIds", {})
                tmdb_id = provider_ids.get("Tmdb")
                if not tmdb_id:
                    continue
                emby_type = item.get("Type", "")
                media_type = "tv" if emby_type == "Series" else "movie"
                results[f"{tmdb_id}:{media_type}"] = True
            total = data.get("TotalRecordCount", 0)
            start += limit
            if start >= total:
                break
        return results

    def get_item_parent_library(self, item_id):
        """
        [优化版] 使用 Ancestors 接口一次性获取层级链，查找父级库
        API: /Items/{Id}/Ancestors
        """
        uid = self._get_user_id()
        # 构造请求 URL
        endpoint = f"emby/Users/{uid}/Items/{item_id}/Ancestors" if uid else f"emby/Items/{item_id}/Ancestors"
        
        try:
            # 发送一次请求，获取所有祖先节点 (列表通常是从下往上，或者从上往下，Emby通常返回完整列表)
            ancestors = self._request("GET", endpoint)
            
            # 遍历祖先节点，寻找类型为媒体库的节点
            # 常见的库类型：CollectionFolder, UserView, BoxSet (合集模式下)
            target_types = ['CollectionFolder', 'UserView', 'BoxSet']
            
            for item in ancestors:
                if item.get('Type') in target_types:
                    # 找到了，直接返回
                    return {"name": item.get('Name'), "id": item.get('Id')}
            
            return None
            
        except Exception as e:
            logger.error(f"反查父级库失败 (ID: {item_id}): {e}")
            return None

    def refresh_library(self, library_id=None):
        try:
            if library_id:
                logger.info(f"刷新指定库: {library_id}")
                endpoint = f"emby/Items/{library_id}/Refresh?Recursive=true&ImageRefreshMode=Default&MetadataRefreshMode=Default&ReplaceAllImages=false&ReplaceAllMetadata=false"
            else:
                endpoint = "emby/Library/Refresh"
            self._request("POST", endpoint)
            return True
        except: return False

    def get_item_info(self, item_id):
        """
        获取媒体详情（用于通知）

        Returns:
            dict: {
                "name": 媒体名称,
                "type": 类型 (Movie/Series/Episode),
                "year": 年份,
                "series_name": 剧集名称 (仅Episode),
                "season": 季数 (仅Episode),
                "episode": 集数 (仅Episode),
                "poster_url": 海报图片URL,
                "overview": 简介
            }
        """
        uid = self._get_user_id()
        endpoint = f"emby/Users/{uid}/Items/{item_id}" if uid else f"emby/Items/{item_id}"

        try:
            info = self._request("GET", endpoint)

            result = {
                "name": info.get("Name", "未知媒体"),
                "type": info.get("Type", ""),
                "year": info.get("ProductionYear", ""),
                "overview": info.get("Overview", ""),
                "poster_url": None,
                "genres": ", ".join(info.get("Genres", [])) if info.get("Genres") else "",
                "community_rating": info.get("CommunityRating"),
                "tagline": info.get("Tagline", ""),
            }

            # 获取海报图片
            if "Primary" in info.get("ImageTags", {}):
                tag = info["ImageTags"]["Primary"]
                result["poster_url"] = f"{self.public_host}/emby/Items/{item_id}/Images/Primary?tag={tag}&quality=90&maxHeight=500"

            # 剧集特殊处理
            if info.get("Type") == "Episode":
                result["series_name"] = info.get("SeriesName", "")
                result["season"] = info.get("ParentIndexNumber", "?")
                result["episode"] = info.get("IndexNumber", "?")
                # 获取剧集海报
                series_id = info.get("SeriesId")
                if series_id and not result["poster_url"]:
                    result["poster_url"] = f"{self.public_host}/emby/Items/{series_id}/Images/Primary?quality=90&maxHeight=500"

                # ★ 获取剧集(Series)级别的评分和类型，而非单集的
                series_id_for_meta = info.get("SeriesId")
                if series_id_for_meta:
                    try:
                        series_endpoint = f"emby/Users/{uid}/Items/{series_id_for_meta}" if uid else f"emby/Items/{series_id_for_meta}"
                        series_info = self._request("GET", series_endpoint)
                        if series_info:
                            series_rating = series_info.get("CommunityRating")
                            if series_rating:
                                result["community_rating"] = series_rating
                            series_genres = series_info.get("Genres", [])
                            if series_genres:
                                result["genres"] = ", ".join(series_genres)
                            series_overview = series_info.get("Overview", "")
                            if series_overview:
                                result["overview"] = series_overview
                            result["series_year"] = series_info.get("ProductionYear", "")
                    except Exception as e:
                        logger.debug(f"获取剧集元数据失败: {e}")

            return result

        except Exception as e:
            logger.error(f"获取媒体详情失败 (ID: {item_id}): {e}")
            return None
