import requests
from typing import Optional, Dict, Any, List
import logging
import json
import os
import re
import base64
import hashlib
import hmac
import time
from urllib import parse
from datetime import datetime
from random import choice
import threading

# 配置日志
logger = logging.getLogger("Douban")

def clean_character_name_static(name: str) -> str:
    """清洗角色名/人名 (补全工具函数)"""
    if not name: return ""
    return re.sub(r'[\s\(\[].*?[\)\]]', '', name).strip()

class DoubanApi:
    """
    豆瓣 API 客户端 (V5.4 - 修复版)
    
    修复记录：
    1. 增加非 JSON 响应捕获 (解决 Expecting value 错误)。
    2. 优化 HTTP 404/403 错误处理，避免作为 Error 打印。
    3. 修复签名算法 (使用 urlparse + quote(safe=''))。
    4. 移除强制代理逻辑，适配直连环境 (但保留 set_proxy 接口)。
    5. 严格区分 apiKey (GET) 和 apikey (POST)。
    6. [本次修复] _ts 时间戳改为秒级，Session 改为实例级以支持多线程。
    """
    
    # --- 冷却配置 ---
    _cooldown_seconds: float = 1.5
    _last_request_time: float = 0.0
    _cooldown_lock = threading.Lock()
    
    # --- 代理配置 (默认为空，直连模式) ---
    _proxies: Optional[Dict] = None
    
    _user_cookie: Optional[str] = None

    # Credentials must be supplied through the environment; never commit
    # third-party API keys to the public source tree.
    _api_secret_key = os.getenv("ALSEMBY_DOUBAN_API_SECRET_KEY", "")
    # GET 请求专用 Key
    _api_key = os.getenv("ALSEMBY_DOUBAN_API_KEY", "")
    
    _base_url = "https://frodo.douban.com/api/v2"
    _api_url = "https://api.douban.com/v2"
    
    _urls = {
        "search": "/search/weixin", 
        "movie_detail": "/movie/", 
        "tv_detail": "/tv/",
    }

    # Frodo UA 池
    _user_agents = [
        "api-client/1 com.douban.frodo/7.22.0.beta9(231) Android/23 product/Mate 40 vendor/HUAWEI model/Mate 40 brand/HUAWEI",
        "api-client/1 com.douban.frodo/7.18.0(230) Android/22 product/MI 9 vendor/Xiaomi model/MI 9 brand/Android",
        "api-client/1 com.douban.frodo/7.45.0(245) Android/31 product/Mi 11 vendor/Xiaomi model/M2011K2C brand/Xiaomi",
    ]

    def __init__(self, cooldown_seconds: float = 1.5, proxies: Optional[Dict] = None):
        if cooldown_seconds is not None:
            DoubanApi._cooldown_seconds = cooldown_seconds
        
        # 即使直连，如果外部强行传入了 proxies，也暂时存一下
        if proxies:
            DoubanApi._proxies = proxies
        
        # [修复] 初始化实例级别的 Session，避免多线程冲突
        self._session = requests.Session()
        self._session.verify = False
        if DoubanApi._proxies:
            self._session.proxies.update(DoubanApi._proxies)

    @classmethod
    def set_proxy(cls, proxy_url: str):
        """
        [兼容性接口] server.py 会调用此方法。
        如果是直连，传入空字符串即可清除代理。
        注意：这会影响新创建的实例，已创建的实例需要重新初始化或手动更新。
        """
        if proxy_url:
            cls._proxies = {"http": proxy_url, "https": proxy_url}
        else:
            cls._proxies = None

    @classmethod
    def _apply_cooldown(cls):
        with cls._cooldown_lock:
            now = time.time()
            elapsed = now - cls._last_request_time
            if elapsed < cls._cooldown_seconds:
                wait_time = cls._cooldown_seconds - elapsed
                time.sleep(wait_time)
            cls._last_request_time = time.time()

    def _ensure_session(self):
        """确保当前实例有可用的 Session"""
        if self._session is None:
            self._session = requests.Session()
            self._session.verify = False 
            if DoubanApi._proxies:
                self._session.proxies.update(DoubanApi._proxies)

    @classmethod
    def _sign(cls, url: str, ts: str, method='GET') -> str:
        """
        [核心] 签名算法 - 完全复刻参考代码
        """
        url_path = parse.urlparse(url).path
        # 关键：safe='' 确保斜杠也被编码，这是豆瓣 API 的特殊要求
        raw_sign = '&'.join([method.upper(), parse.quote(url_path, safe=''), ts])
        return base64.b64encode(hmac.new(cls._api_secret_key.encode(), raw_sign.encode(), hashlib.sha1).digest()).decode()

    def _make_error_dict(self, error_code: str, message: str) -> Dict[str, Any]:
        return {"error": error_code, "message": message}

    def __invoke(self, url: str, **kwargs) -> Dict[str, Any]:
        """通用 GET 请求执行器"""
        DoubanApi._apply_cooldown()
        self._ensure_session()
        
        req_url = DoubanApi._base_url + url
        
        # 注意：GET 请求使用的是 _api_key (0dad...) 和 apiKey (驼峰)
        params = {'apiKey': DoubanApi._api_key, **kwargs}
        
        # [核心修复] _ts 时间戳改为秒级 Unix 时间戳，解决 400 Bad Request
        ts = params.pop('_ts', str(int(time.time())))
        
        # 计算签名
        sig = DoubanApi._sign(url=req_url, ts=ts, method='GET')
        params.update({
            'os_rom': 'android', 
            '_ts': ts, 
            '_sig': sig
        })
        
        headers = {
            'User-Agent': choice(DoubanApi._user_agents)
        }
        
        try:
            # 增加 timeout 防止卡死，使用实例 self._session
            resp = self._session.get(req_url, params=params, headers=headers, timeout=15)
            
            # [核心修复] 捕获非 JSON 响应 (如被防火墙拦截返回 HTML)
            try:
                data = resp.json()
            except json.JSONDecodeError:
                # 截取前 100 字符，通常能看出是不是被封了
                preview = resp.text[:100].replace('\n', ' ')
                logger.warning(f"  [Douban] API 返回非 JSON 数据 ({resp.status_code}): {preview}...")
                return self._make_error_dict("json_error", f"Invalid JSON response: {preview[:30]}")

            if data.get("code") == 1080:
                return self._make_error_dict("rate_limit", data.get("msg", "Rate Limit"))
                
            resp.raise_for_status()
            return data

        except requests.exceptions.HTTPError as e:
            # 404 是正常的业务逻辑 (未找到条目)，不应视为系统错误
            if e.response.status_code == 404:
                return self._make_error_dict("not_found", "Item not found")
            logger.warning(f"  [Douban] HTTP Error: {e}")
            return self._make_error_dict("http_error", str(e))
        except Exception as e:
            logger.error(f"  [Douban] Request Error: {e}")
            return self._make_error_dict("network_error", str(e))

    def get_details_from_douban_link(self, douban_link: str, mtype: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        从豆瓣链接获取详情
        """
        if not douban_link: return None
        
        match = re.search(r'/(?:movie|tv|subject)/(\d+)', douban_link)
        if not match: return None

        douban_id = match.group(1)
        
        # 逻辑：优先尝试推断的类型，如果 404/Error 再尝试另一种
        # Emby 传入的 mtype 可能是 'Series' 或 'Movie'
        primary_type = 'tv' if mtype and mtype.lower() in ['series', 'tv'] else 'movie'
        
        # 第一次尝试
        endpoint = self._urls["tv_detail"] if primary_type == 'tv' else self._urls["movie_detail"]
        res = self.__invoke(endpoint + douban_id)
        
        # 如果失败，交换类型再试一次
        if res.get("error") or res.get("code"):
            alt_type = 'movie' if primary_type == 'tv' else 'tv'
            # logger.debug(f"  [Douban] 主类型 {primary_type} 失败，尝试备用类型 {alt_type}...")
            alt_endpoint = self._urls["tv_detail"] if alt_type == 'tv' else self._urls["movie_detail"]
            res = self.__invoke(alt_endpoint + douban_id)
            if not (res.get("error") or res.get("code")):
                primary_type = alt_type # 修正成功

        if res.get("error") or res.get("code"):
            # logger.warning(f"  [Douban] 获取详情失败 ID: {douban_id}")
            return None

        # 提取数据
        imdb_id = res.get("imdb") or res.get("imdb_id")
        if not imdb_id and "attrs" in res and "imdb" in res["attrs"]:
             imdb_vals = res["attrs"]["imdb"]
             if imdb_vals: imdb_id = imdb_vals[0]

        aliases = res.get("aka", [])
        if isinstance(aliases, list):
            aliases = [x.strip() for x in aliases if len(x) < 50]

        return {
            "id": douban_id,
            "title": res.get("title"),
            "original_title": res.get("original_title"),
            "aliases": aliases,
            "year": res.get("year"),
            "imdb_id": imdb_id,
            "rating": res.get("rating", {}).get("value"),
            "intro": res.get("intro"),
            "poster": res.get("pic", {}).get("large"),
            "type": "Series" if primary_type == 'tv' else "Movie"
        }

    def search(self, keyword: str, count: int = 3) -> List[Dict[str, Any]]:
        res = self.__invoke(self._urls["search"], q=keyword, count=count)
        return res.get("items", [])

    # ========== 推荐榜接口 ==========

    def get_hot_movies(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣热门电影"""
        return self.__invoke("/subject_collection/movie_hot/items", start=start, count=count)

    def get_hot_tv(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣热门剧集"""
        return self.__invoke("/subject_collection/tv_hot/items", start=start, count=count)

    def get_hot_anime(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣热门动漫"""
        return self.__invoke("/subject_collection/tv_animation/items", start=start, count=count)

    def get_showing(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣正在上映"""
        return self.__invoke("/subject_collection/movie_showing/items", start=start, count=count)

    def get_new_movies(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣最新电影 — 使用 movie_latest 合集"""
        return self.__invoke("/subject_collection/movie_latest/items", start=start, count=count)

    def get_new_tv(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣最新剧集 — 使用 tv_domestic 合集（暂无 tv_latest，用国产剧替代）"""
        return self.__invoke("/subject_collection/tv_domestic/items", start=start, count=count)

    def get_top250(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣 Top 250"""
        return self.__invoke("/subject_collection/movie_top250/items", start=start, count=count)

    def get_chinese_tv_weekly(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣华语口碑剧集榜"""
        return self.__invoke("/subject_collection/tv_chinese_best_weekly/items", start=start, count=count)

    def get_global_tv_weekly(self, start: int = 0, count: int = 20) -> Dict[str, Any]:
        """豆瓣全球口碑剧集榜"""
        return self.__invoke("/subject_collection/tv_global_best_weekly/items", start=start, count=count)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    api = DoubanApi()
    print("Testing DoubanApi (Direct Connect)...")
    # 测试代码
    # print(api.get_details_from_douban_link("https://movie.douban.com/subject/1292052/"))
