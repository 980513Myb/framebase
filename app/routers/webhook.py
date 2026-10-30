# app/routers/webhook.py
import os
import json
from fastapi import APIRouter, Request, HTTPException

from app.schemas import WebhookConfigModel
from app.dependencies import webhook_debouncer
from app.services.task_service import execute_task_logic
from app.services.wechat_service import wechat_notify_service
from core.configs import WEBHOOK_CONFIG_FILE, CONFIG_FILE
from core.emby_client import EmbyClient
from core.logger import logger

router = APIRouter(tags=["Webhook"])

PLAYBACK_EVENTS = {"playback.start", "playback.started"}
COVER_EVENTS = {"library.new", "item.added", "library.scan_complete"}
DELETE_EVENTS = {"item.removed", "library.deleted"}
TEST_EVENTS = {
    "test",
    "webhook.test",
    "system.webhooktest",
    "system.webhook.test",
    "system.notificationtest",
}
EVENT_ALIASES = {
    "media.play": "playback.start",
    "media.added": "item.added",
    "media.remove": "item.removed",
    "media.removed": "item.removed",
}


def _normalize_payload(data):
    """Normalize current Emby payloads and the legacy Webhooks plugin format."""
    if not isinstance(data, dict):
        return {}

    normalized = dict(data)
    raw_event = (
        data.get("Event")
        or data.get("event")
        or data.get("NotificationType")
        or data.get("notificationType")
        or ""
    )
    normalized["Event"] = EVENT_ALIASES.get(str(raw_event).strip().lower(), str(raw_event).strip().lower())

    if not isinstance(normalized.get("Item"), dict):
        item_type = data.get("ItemType") or data.get("itemType") or ""
        type_aliases = {
            "movies": "Movie",
            "movie": "Movie",
            "tvshows": "Episode",
            "episode": "Episode",
            "series": "Series",
        }
        normalized["Item"] = {
            "Id": data.get("ItemId") or data.get("ItemID") or data.get("itemId"),
            "Name": data.get("ItemName") or data.get("itemName"),
            "Type": type_aliases.get(str(item_type).lower(), item_type),
            "SeriesName": data.get("ItemNameGrandparent") or data.get("ItemNameParent"),
            "ParentIndexNumber": data.get("ItemParentIndex"),
            "IndexNumber": data.get("ItemIndex"),
            "Path": data.get("ItemPath") or data.get("Path"),
        }

    if not isinstance(normalized.get("User"), dict):
        normalized["User"] = {"Name": data.get("UserName") or data.get("userName")}
    if not isinstance(normalized.get("Session"), dict):
        normalized["Session"] = {
            "Client": data.get("AppName") or data.get("Client"),
            "DeviceName": data.get("DeviceName"),
            "RemoteEndPoint": data.get("RemoteEndPoint") or data.get("RemoteEndpoint") or data.get("DeviceIP"),
            "UserName": data.get("UserName") or data.get("userName"),
        }
    if not isinstance(normalized.get("Server"), dict):
        normalized["Server"] = {"Name": data.get("ServerName") or data.get("serverName")}

    return normalized


def _load_webhook_config():
    if os.path.exists(WEBHOOK_CONFIG_FILE):
        try:
            with open(WEBHOOK_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            logger.error(f"[Webhook] 配置读取失败: {exc}")
    return {"enabled": False, "engine": "classic", "preset": "", "mode": "random"}


def _load_servers():
    if not os.path.exists(CONFIG_FILE):
        return []
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f).get("servers", [])
    except Exception as exc:
        logger.error(f"[Webhook] Emby 配置读取失败: {exc}")
        return []


def _send_playback_notification(data, servers):
    item_data = data.get("Item") or {}
    session_data = data.get("Session") or {}
    user_data = data.get("User") or {}
    server_data = data.get("Server") or {}
    item_id = item_data.get("Id")
    item_name = item_data.get("Name") or "未知媒体"
    item_type = item_data.get("Type") or ""
    media_type = "movie" if item_type == "Movie" else "series" if item_type in ("Series", "Episode") else "other"
    poster_url = ""
    poster_data = None
    poster_content_type = None
    original_name = item_data.get("SeriesName") or item_name
    overview = item_data.get("Overview") or ""
    rating = str(item_data.get("CommunityRating") or "")
    genres = ", ".join(item_data.get("Genres") or [])
    tagline = item_data.get("Tagline") or ""
    emby_name = server_data.get("Name") or "Emby"

    if item_type == "Episode":
        series_name = item_data.get("SeriesName") or item_name
        season = item_data.get("ParentIndexNumber", "?")
        episode = item_data.get("IndexNumber", "?")
        item_name = f"{series_name} S{season}E{episode} - {item_name}"

    for server in servers:
        try:
            client = EmbyClient(server["host"], server["key"], server.get("public_host"), server.get("user_name"))
            item_info = client.get_item_info(item_id) if item_id else None
            if not item_info:
                continue
            emby_name = server_data.get("Name") or server.get("name") or emby_name
            poster_url = item_info.get("poster_url") or ""
            if poster_url:
                poster_data, poster_content_type = client.get_image_data(poster_url)
            overview = item_info.get("overview") or overview
            tagline = item_info.get("tagline") or tagline
            rating_value = item_info.get("community_rating")
            rating = str(round(rating_value, 1)) if rating_value else rating
            genres = item_info.get("genres") or genres
            if item_info.get("type") == "Episode":
                series_name = item_info.get("series_name") or original_name
                season = item_info.get("season", "?")
                episode = item_info.get("episode", "?")
                episode_name = item_info.get("name") or item_data.get("Name") or ""
                item_name = f"{series_name} S{season}E{episode}" + (f" - {episode_name}" if episode_name else "")
                original_name = series_name
            else:
                item_name = item_info.get("name") or item_name
                original_name = item_name
            break
        except Exception as exc:
            logger.debug(f"[Webhook] 播放信息回查失败: {exc}")

    client_name = session_data.get("Client") or session_data.get("AppName") or ""
    device_name = session_data.get("DeviceName") or ""
    device_ip = (
        session_data.get("RemoteEndPoint")
        or session_data.get("RemoteEndpoint")
        or session_data.get("DeviceIP")
        or data.get("RemoteEndPoint")
        or data.get("RemoteEndpoint")
        or data.get("DeviceIP")
        or ""
    )
    client_parts = [client_name, device_name]
    client_info = " / ".join(str(part) for part in client_parts if part) or "未知客户端"
    user_name = user_data.get("Name") or session_data.get("UserName") or "未知用户"
    notified = wechat_notify_service.notify_playback(
        item_name=item_name,
        emby_name=emby_name,
        poster_url=poster_url,
        original_name=original_name,
        media_type=media_type,
        overview=overview,
        rating=rating,
        genres=genres,
        tagline=tagline,
        user_name=user_name,
        client_info=client_info,
        client_name=client_name,
        device_name=device_name,
        device_ip=device_ip,
        poster_data=poster_data,
        poster_content_type=poster_content_type,
    )
    logger.info(f"[Webhook] 播放通知处理完成: {item_name} | sent={notified}")
    return notified

@router.get("/api/webhook/config")
def get_webhook_config():
    return _load_webhook_config()

@router.post("/api/webhook/config")
def save_webhook_config(cfg: WebhookConfigModel):
    try:
        with open(WEBHOOK_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg.model_dump(), f, indent=4, ensure_ascii=False)
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/webhook")
async def emby_webhook_trigger(request: Request):
    wh_config = _load_webhook_config()
    cover_automation_enabled = bool(wh_config.get("enabled", False))

    try:
        content_type = request.headers.get("content-type", "")
        data = {}
        if "application/json" in content_type:
            data = await request.json()
        else:
            form = await request.form()
            if 'data' in form:
                data = json.loads(form['data'])
            else:
                data = dict(form)
    except Exception as e:
        logger.warning(f"[Webhook] Payload parse failed: {e}")
        return {"status": "error", "reason": f"Payload Error: {e}"}

    data = _normalize_payload(data)
    event_type = data.get("Event", "")
    item_data = data.get("Item") or {}
    item_id = item_data.get("Id") if isinstance(item_data, dict) else None
    logger.info(f"[Webhook] Received event='{event_type or '<empty>'}' | item_id={item_id or '-'}")

    if event_type in TEST_EVENTS:
        notified = wechat_notify_service.send_message("FrameBase 已成功收到 Emby Webhook 测试通知")
        logger.info(f"[Webhook] Test notification handled | sent={notified}")
        return {"status": "ok", "action": "webhook_test", "notified": notified}

    watched_events = PLAYBACK_EVENTS | COVER_EVENTS | DELETE_EVENTS

    if event_type not in watched_events:
        logger.warning(f"[Webhook] Ignored unsupported event='{event_type or '<empty>'}'")
        return {"status": "ignored", "reason": f"Event '{event_type}' not watched"}

    servers = _load_servers()

    if event_type in PLAYBACK_EVENTS:
        notified = _send_playback_notification(data, servers)
        return {"status": "ok", "action": "playback_notification", "notified": notified}

    # ========== 删除事件：清除缓存 ==========
    if event_type in DELETE_EVENTS:
        import core.emby_cache as emby_cache
        item_data_del = data.get("Item", {})
        provider_ids = item_data_del.get("ProviderIds", {})
        tmdb_id = provider_ids.get("Tmdb")
        if tmdb_id:
            item_type_str = item_data_del.get("Type", "")
            media_type = "tv" if item_type_str in ("Series", "Season", "Episode") else "movie"
            emby_cache.remove_id(tmdb_id, media_type)
            logger.info(f"[Webhook] 缓存已清除: {tmdb_id}:{media_type}")
        else:
            # payload 没有 ProviderIds，尝试用 Item ID 查详情
            item_id_del = item_data_del.get("Id")
            if item_id_del and os.path.exists(CONFIG_FILE):
                try:
                    with open(CONFIG_FILE, 'r') as f:
                        servers_list = json.load(f).get('servers', [])
                    for svr in servers_list:
                        try:
                            client_tmp = EmbyClient(svr['host'], svr['key'], svr.get('public_host'), svr.get('user_name'))
                            info = client_tmp._request("GET", f"emby/Items/{item_id_del}")
                            prov = info.get("ProviderIds", {})
                            tmdb_val = prov.get("Tmdb")
                            if tmdb_val:
                                m_type = "tv" if info.get("Type") in ("Series",) else "movie"
                                emby_cache.remove_id(tmdb_val, m_type)
                                logger.info(f"[Webhook] 缓存已清除(回查): {tmdb_val}:{m_type}")
                                break
                        except Exception:
                            continue
                except Exception:
                    pass
        return {"status": "ok", "action": "cache_evicted"}

    item_data = data.get("Item", {})
    target_item_id = item_data.get("Id")
    item_path = item_data.get("Path") 
    
    if not item_path and target_item_id:
        logger.info(f"[Webhook] Path missing in payload, will try to fetch for ID: {target_item_id}")

    logger.info(f"[Webhook] Processing '{event_type}' | ID: {target_item_id} | Path: {item_path}")

    targets = []
    preset_name = wh_config.get("preset")

    # 遍历服务器，查找该 Webhook 属于哪个库
    for svr in servers:
        try:
            client = EmbyClient(svr['host'], svr['key'], svr.get('public_host'), svr.get('user_name'))
            server_libs = client.get_libraries() 
            matched_lib = None
            
            # 1. 尝试直接匹配库ID (如果是 library.new 事件)
            matched_lib = next((l for l in server_libs if str(l['id']) == str(target_item_id)), None)

            # 2. 尝试匹配路径 (如果是 item.added 事件)
            if not matched_lib and item_path:
                norm_item_path = item_path.replace('\\', '/')
                matched_lib = next(
                    (lib for lib in server_libs if lib.get('paths') and 
                     any(norm_item_path.startswith(loc.replace('\\', '/')) for loc in lib.get('paths'))),
                    None
                )

            # 3. 尝试反查 API 获取路径再匹配
            if not matched_lib and target_item_id and not item_path:
                try:
                    full_info = client._request("GET", f"emby/Items/{target_item_id}")
                    fetched_path = full_info.get("Path")
                    if fetched_path:
                        norm_fetched = fetched_path.replace('\\', '/')
                        matched_lib = next(
                            (lib for lib in server_libs if lib.get('paths') and 
                             any(norm_fetched.startswith(loc.replace('\\', '/')) for loc in lib.get('paths'))),
                            None
                        )
                        logger.info(f"[Webhook] Fetched path match: {fetched_path} -> {matched_lib['name'] if matched_lib else 'None'}")
                except: pass

            if matched_lib:
                logger.info(f"[Webhook] Match Found: {matched_lib['name']} (ID: {matched_lib['id']}) on {svr.get('name', 'Server')}")

                # 入库通知与自动封面开关相互独立。
                try:
                    item_name = item_data.get("Name", "未知媒体")
                    item_type = item_data.get("Type", "")
                    year = item_data.get("ProductionYear", "")
                    media_type = "movie" if item_type == "Movie" else "series" if item_type == "Episode" or item_type == "Series" else "other"
                    poster_url = ""
                    season = ""
                    episode = ""
                    original_name = ""# 用于 TMDB 搜索
                    overview = ""
                    rating = ""
                    genres = ""
                    tagline = ""

                    # 获取媒体详情和海报
                    if target_item_id and media_type in ["movie", "series"]:
                        try:
                            item_info = client.get_item_info(target_item_id)
                            if item_info:
                                year = item_info.get("year", year)
                                poster_url = item_info.get("poster_url") or ""
                                overview = item_info.get("overview", "") or ""
                                tagline = item_info.get("tagline", "") or ""
                                cr = item_info.get("community_rating")
                                rating = str(round(cr, 1)) if cr else ""
                                genres = item_info.get("genres", "") or ""

                                # 剧集特殊处理：使用剧集名称，构建完整标题
                                if item_info.get("type") == "Episode":
                                    series_name = item_info.get("series_name", item_name)
                                    season = str(item_info.get("season", "?"))
                                    episode = str(item_info.get("episode", "?"))
                                    episode_title = item_info.get("name", "")
                                    original_name = series_name# TMDB 搜索用剧集名
                                    # 构建完整标题：剧集名 S1E1 - 单集名
                                    if episode_title and episode_title != series_name:
                                        item_name = f"{series_name} S{season}E{episode} - {episode_title}"
                                    else:
                                        item_name = f"{series_name} S{season}E{episode}"
                                    # 如果获取到了剧集年份，使用剧集年份
                                    series_year = item_info.get("series_year")
                                    if series_year:
                                        year = series_year
                                else:
                                    item_name = item_info.get("name", item_name)
                                    original_name = item_name
                        except Exception as e:
                            logger.debug(f"[Webhook] 获取媒体海报失败: {e}")

                    if event_type in {"item.added", "library.new"} and media_type in ["movie", "series"]:
                        notify_kwargs = dict(
                            media_name=item_name,
                            media_type=media_type,
                            library_name=matched_lib['name'],
                            year=str(year) if year else "",
                            poster_url=poster_url,
                            original_name=original_name,
                            overview=overview,
                            rating=rating,
                            genres=genres,
                            tagline=tagline,
                        )
                        wechat_notify_service.notify_media_added(**notify_kwargs)
                except Exception as notify_err:
                    logger.debug(f"[Webhook] 发送入库通知失败: {notify_err}")

                targets.append({
                    "host": svr['host'],
                    "key": svr['key'],
                    "public_host": svr.get('public_host'),
                    "user_name": svr.get('user_name'),
                    "library_id": matched_lib['id'],
                    "library_name": matched_lib['name'],
                })
            else:
                pass

        except Exception as e:
            logger.error(f"-> Error checking server {svr.get('name')}: {e}")

    if not targets:
        return {"status": "ignored", "reason": f"Item not resolved to any library"}

    if not cover_automation_enabled:
        return {
            "status": "ok",
            "action": "notification_only",
            "cover_automation": False,
            "targets_resolved": len(targets),
        }

    if not preset_name:
        return {"status": "error", "reason": "No Preset Selected"}

    mode = wh_config.get("mode", "random")
    triggered_count = 0
    
    # 使用防抖器调度任务
    for target in targets:
        lib_id = target['library_id']
        lib_name = target['library_name']

        webhook_debouncer.schedule(
            lib_id,
            execute_task_logic,
            [preset_name, [target], mode, f"Webhook: {lib_name}"]
        )
        triggered_count += 1

    return {
        "status": "queued",
        "cover_automation": True,
        "targets_debounced": triggered_count,
    }
