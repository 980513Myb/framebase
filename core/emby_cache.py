# core/emby_cache.py
# Emby 媒体库持久化缓存 — JSON 文件 + 线程安全

import os
import json
import time
import threading
from core.configs import EMBY_LIBRARY_CACHE_FILE

_lock = threading.Lock()


def load_cache() -> dict:
    """加载完整缓存，格式: { "tmdb_id:type": True, ..., "_meta": {...} }"""
    if not os.path.exists(EMBY_LIBRARY_CACHE_FILE):
        return {}
    try:
        with open(EMBY_LIBRARY_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(data: dict):
    """原子写入缓存文件"""
    tmp = EMBY_LIBRARY_CACHE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)
    os.replace(tmp, EMBY_LIBRARY_CACHE_FILE)


def check_ids(pairs: list) -> dict:
    """批量查询 [(tmdb_id, type)]，返回命中的 { tmdb_id: True }"""
    with _lock:
        cache = load_cache()
    result = {}
    for tmdb_id, media_type in pairs:
        key = f"{tmdb_id}:{media_type}"
        if cache.get(key):
            result[str(tmdb_id)] = True
    return result


def add_ids(entries: dict):
    """增量写入 { "tmdb_id:type": True }"""
    with _lock:
        cache = load_cache()
        cache.update(entries)
        # 更新 meta
        count = sum(1 for k in cache if k != "_meta")
        cache["_meta"] = {"last_sync": time.time(), "count": count}
        _save_cache(cache)


def remove_id(tmdb_id, media_type: str):
    """删除单条缓存"""
    key = f"{tmdb_id}:{media_type}"
    with _lock:
        cache = load_cache()
        if key in cache:
            del cache[key]
            count = sum(1 for k in cache if k != "_meta")
            cache["_meta"] = {"last_sync": time.time(), "count": count}
            _save_cache(cache)


def replace_all(entries: dict):
    """全量替换缓存（同步用）"""
    with _lock:
        cache = dict(entries)
        count = sum(1 for k in cache if k != "_meta")
        cache["_meta"] = {"last_sync": time.time(), "count": count}
        _save_cache(cache)
