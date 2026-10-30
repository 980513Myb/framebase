# app/dependencies.py
import os
import json
import uuid
import time
import gc
import logging
from concurrent.futures import ThreadPoolExecutor

# 引入配置
from core.configs import CONFIG_FILE, TRANSLATIONS_FILE
import core.tmdb as tmdb_module
import core.douban as douban_module
from core.logger import logger

# 全局线程池
MAX_WORKERS = min(4, (os.cpu_count() or 1) + 1)
GLOBAL_EXECUTOR = ThreadPoolExecutor(max_workers=MAX_WORKERS)

# 任务状态存储
ACTIVE_TASKS = {}

# 全局翻译缓存
global_translations = {}

def load_translations_data():
    """加载翻译数据"""
    global global_translations
    if os.path.exists(TRANSLATIONS_FILE):
        try:
            with open(TRANSLATIONS_FILE, "r", encoding="utf-8") as f:
                global_translations = json.load(f)
        except:
            pass
    return global_translations

# 初始化加载一次
load_translations_data()

def update_task_progress(run_id, name, percent, status="running"):
    """更新任务进度"""
    cancel_req = False
    if run_id in ACTIVE_TASKS:
        cancel_req = ACTIVE_TASKS[run_id].get("cancel_requested", False)
    
    ACTIVE_TASKS[run_id] = {
        "name": name, 
        "percent": percent, 
        "status": status, 
        "updated_at": time.time(), 
        "cancel_requested": cancel_req
    }

def cleanup_stale_tasks():
    """清理过期任务记录"""
    now = time.time()
    to_remove = [
        k for k, v in ACTIVE_TASKS.items() 
        if (v['status'] in ['finished', 'error', 'stopped'] and (now - v.get('updated_at', 0)) > 1800) 
        or (now - v.get('updated_at', 0)) > 86400
    ]
    for k in to_remove:
        del ACTIVE_TASKS[k]
    if to_remove:
        gc.collect()

def apply_proxy_settings():
    """应用外部服务代理设置"""
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            proxy_url = settings.get('proxy_url', '')
            tmdb_module.set_proxy(proxy_url)
            douban_module.DoubanApi.set_proxy(proxy_url)
            logger.info(f"[System] 外部服务代理配置已更新: {proxy_url if proxy_url else '关闭'}")
        except Exception as e:
            logger.error(f"[System] 应用外部服务代理失败: {e}")

# --- 追加到 app/dependencies.py 末尾 ---
import threading
from threading import Timer
from core.configs import DEVICE_ID_FILE

# Webhook 防抖管理器
class WebhookDebouncer:
    def __init__(self, delay=10):
        self.delay = delay 
        self.timers = {}
        self.lock = threading.Lock()

    def schedule(self, library_id, func, *args, **kwargs):
        with self.lock:
            if library_id in self.timers:
                logger.info(f"[Webhook] Reset timer for library: {library_id}")
                self.timers[library_id].cancel()

            timer = Timer(self.delay, self._run, args=(library_id, func, args, kwargs))
            self.timers[library_id] = timer
            timer.start()
            logger.info(f"[Webhook] Scheduled task for library: {library_id} in {self.delay}s")

    def _run(self, library_id, func, args, kwargs):
        with self.lock:
            if library_id in self.timers:
                del self.timers[library_id]
        func(*args[0], **kwargs)

# 全局防抖实例
webhook_debouncer = WebhookDebouncer(delay=10)

def get_device_fingerprint():
    """获取或生成设备指纹"""
    if os.path.exists(DEVICE_ID_FILE):
        try:
            with open(DEVICE_ID_FILE, 'r', encoding='utf-8') as f:
                code = f.read().strip()
                if code and len(code) >= 8: return code
        except: pass
    try: 
        new_code = uuid.uuid4().hex[:12].upper()
    except: 
        new_code = "UNKNOWN-DEVICE"
    try:
        with open(DEVICE_ID_FILE, 'w', encoding='utf-8') as f: f.write(new_code)
    except: pass
    return new_code
