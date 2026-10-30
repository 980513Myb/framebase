# app/routers/server.py
import os
import json
from fastapi import APIRouter, HTTPException
from app.schemas import ConnectionRequest, EmbySearchRequest, EmbyItemImagesRequest, EmbyRandomPoolRequest
from core.configs import CONFIG_FILE, TASKS_FILE, BACKUPS_DIR, FONTS_DIR
from core.emby_client import EmbyClient
from app.dependencies import apply_proxy_settings

router = APIRouter(tags=["Server"])


def _client(req):
    return EmbyClient(req.host, req.key, req.public_host, req.user_name)

@router.post("/api/connect")
def connect(req: ConnectionRequest):
    client = _client(req)
    check = client.check_connection()
    if check.get("ok"):
        try:
            return {"status": "ok", "libraries": client.get_libraries()}
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))
    status_code = check.get("status_code")
    detail = check.get("message") or "Emby 连接失败"
    if status_code in (401, 403):
        raise HTTPException(status_code=status_code, detail=detail)
    raise HTTPException(status_code=400, detail=detail)

@router.post("/api/library_covers")
def get_library_covers(req: ConnectionRequest):
    client = _client(req)
    try:
        libs = client.get_libraries_with_covers() if hasattr(client, 'get_libraries_with_covers') else client.get_libraries()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"libraries": libs}

@router.post("/api/emby/search")
def emby_search(req: EmbySearchRequest):
    client = _client(req)
    return {"items": client.search_items(req.query, req.library_id, req.type)}

@router.post("/api/emby/get_images")
def emby_get_images(req: EmbyItemImagesRequest):
    client = _client(req)
    return {"images": client.get_item_images(req.item_id, req.type)}

@router.post("/api/emby/random_pool")
def emby_random_pool(req: EmbyRandomPoolRequest):
    client = _client(req)
    return {"images": client.get_random_pool(req.library_id, req.type, req.limit)}

@router.post("/api/save")
def save_config(config: dict):
    current_config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f: current_config = json.load(f)
        except: pass

    current_config.update(config)

    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(current_config, f, indent=4, ensure_ascii=False)

    # 刷新配置缓存
    from core.configs import global_config
    global_config.load()
    try:
        import config_manager
        config_manager._settings_cache = None
        config_manager._settings_cache_time = 0
    except Exception:
        pass

    # 仅在代理相关配置更新时才刷新代理设置
    proxy_related_keys = ['proxy_url', 'tmdb_key']
    if any(key in config for key in proxy_related_keys):
        apply_proxy_settings()
    return {"status": "saved"}

@router.get("/api/load")
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f: return json.load(f)
    return {}

@router.get("/api/dashboard_stats")
def get_dashboard_stats():
    task_count = 0
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, 'r') as f:
                task_count = len(json.load(f))
        except: pass
    suite_count = len([d for d in os.listdir(BACKUPS_DIR) if os.path.isdir(os.path.join(BACKUPS_DIR, d))]) if os.path.exists(BACKUPS_DIR) else 0
    font_count = len([f for f in os.listdir(FONTS_DIR) if f.lower().endswith(('.ttf', '.otf'))]) if os.path.exists(FONTS_DIR) else 0
    return {
        "tasks": task_count,
        "auto_tasks": task_count,
        "backups": suite_count,
        "fonts": font_count,
    }
