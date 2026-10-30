import os
import json
import uuid
import base64
import gc
import copy
import traceback
from concurrent.futures import as_completed

# 调度器相关
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 引入核心模块
from core.emby_client import EmbyClient
from core.engine import PosterEngine
from core.asset_limits import resolve_asset_limits
from core.configs import TEMPLATES_DIR, FONTS_DIR, LAYOUTS_DIR, TASKS_FILE
from core.logger import logger
from app.services.title_mapping import apply_title_mapping
from app.services.wechat_service import wechat_notify_service

# 引入依赖
from app.dependencies import (
    ACTIVE_TASKS, 
    GLOBAL_EXECUTOR, 
    update_task_progress, 
    global_translations
)

# ==========================================
# 1. 任务执行逻辑 (封面生成)
# ==========================================
def _notify_task_complete_safe(task_name, status, detail, posters_count=0):
    try:
        return wechat_notify_service.notify_task_complete(
            task_name,
            status=status,
            detail=detail,
            posters_count=posters_count,
        )
    except Exception as exc:
        logger.warning(f"[TaskService] 海报通知发送失败: {exc}")
        return False


def execute_task_logic(
    preset_filename,
    targets,
    mode="random",
    task_name="Unknown",
    fallback_to_next_backdrop=True,
):
    """
    通用任务执行逻辑 (生成封面)
    """
    run_id = str(uuid.uuid4())
    update_task_progress(run_id, f"任务: {task_name}", 0, "running")
    logger.info(f">>> [任务: {task_name}] 开始执行...")
    
    preset_path = os.path.join(TEMPLATES_DIR, preset_filename)
    if not os.path.exists(preset_path):
        update_task_progress(run_id, f"任务失败: 预设丢失", 100, "error")
        _notify_task_complete_safe(task_name, status="failed", detail="预设不存在")
        return {"status": "error"}
    
    try:
        with open(preset_path, "r", encoding="utf-8") as f:
            preset_data = json.load(f)
            base_config = preset_data.get("config", {}) 
            base_config['engine'] = preset_data.get("engine", "classic")
    except:
        update_task_progress(run_id, f"任务失败: 预设损坏", 100, "error")
        _notify_task_complete_safe(task_name, status="failed", detail="预设文件损坏")
        return {"status": "error"}
        
    engine = PosterEngine(fonts_dir=FONTS_DIR, layouts_dir=LAYOUTS_DIR)
    total = len(targets)
    
    def process_target(target_obj):
        # 兼容 Pydantic 对象和 dict
        t = target_obj if isinstance(target_obj, dict) else target_obj.model_dump()
        try:
            run_config = copy.deepcopy(base_config)
            library_name = t.get('library_name', 'Unknown')
            run_config = apply_title_mapping(run_config, library_name, global_translations)
            
            client = EmbyClient(t['host'], t['key'], t.get('public_host'), t.get('user_name'))
            p_limit, b_limit = resolve_asset_limits(run_config)
            
            assets = client.get_assets(
                t['library_id'],
                mode=mode,
                poster_limit=p_limit,
                backdrop_limit=b_limit,
                fallback_to_next_backdrop=fallback_to_next_backdrop,
            )
            
            if not assets or (not assets.get('posters') and not assets.get('bg_url') and not assets.get('backdrops')):
                return False
                
            img_b64 = engine.draw(run_config, assets)
            img_data = base64.b64decode(img_b64)
            
            if client.upload_cover(t['library_id'], img_data):
                return True
        except Exception as e:
            logger.error(f"    ❌ {t.get('library_name')}: 异常 {e}")
        return False

    success_count = 0
    fail_count = 0
    
    futures = [GLOBAL_EXECUTOR.submit(process_target, t) for t in targets]
    
    for i, future in enumerate(as_completed(futures)):
        # 检查取消信号
        if ACTIVE_TASKS.get(run_id, {}).get("cancel_requested"):
            for f in futures: f.cancel()
            update_task_progress(run_id, f"任务: {task_name} (已停止)", int(((i) / total) * 100), "error")
            _notify_task_complete_safe(task_name, status="failed", detail="任务已停止", posters_count=success_count)
            return {"status": "stopped"}
            
        if future.result():
            success_count += 1
        else:
            fail_count += 1
            
        percent = int(((i + 1) / total) * 100)
        update_task_progress(run_id, f"任务: {task_name}", percent, "running")
        
    logger.info(f">>> [任务: {task_name}] 执行结束. 成功: {success_count}, 失败: {fail_count}")
    update_task_progress(run_id, f"任务: {task_name}", 100, "finished")
    notify_status = "success" if fail_count == 0 else "failed"
    _notify_task_complete_safe(
        task_name,
        status=notify_status,
        detail=f"成功 {success_count} 个，失败 {fail_count} 个",
        posters_count=success_count,
    )
    gc.collect() 
    return {"status": "ok"}

# ==========================================
# 2. 定义 TaskService 类
# ==========================================
class TaskService:
    def __init__(self):
        # 初始化后台调度器
        self.scheduler = BackgroundScheduler()
        self.active_tasks = {} # 内存中记录任务配置，用于前端展示

    def get_tasks(self):
        """获取当前所有任务"""
        return list(self.active_tasks.values())

    def load_active_jobs(self):
        """启动时从 tasks.json 恢复已启用的定时任务到调度器"""
        if not os.path.exists(TASKS_FILE):
            return
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                tasks = json.load(f)
        except Exception as e:
            logger.error(f"[TaskService] 读取 tasks.json 失败: {e}")
            return

        loaded = 0
        for task in tasks:
            if not task.get("enabled"):
                continue
            cron_str = task.get("cron", "")
            if len(cron_str.split()) != 5:
                continue
            try:
                preset = task["preset"]
                targets = task["targets"]
                mode = task.get("mode", "random")
                fallback_to_next_backdrop = task.get("fallback_to_next_backdrop", True)
                name = task.get("name", "Unknown")
                task_id = task["id"]

                def job_wrapper(p=preset, t=targets, m=mode, n=name, f=fallback_to_next_backdrop):
                    execute_task_logic(
                        preset_filename=p,
                        targets=t,
                        mode=m,
                        task_name=n,
                        fallback_to_next_backdrop=f,
                    )

                self.scheduler.add_job(
                    job_wrapper,
                    CronTrigger.from_crontab(cron_str),
                    id=str(task_id),
                    replace_existing=True
                )
                self.active_tasks[str(task_id)] = task
                loaded += 1
            except Exception as e:
                logger.error(f"[TaskService] 恢复任务失败 {task.get('name')}: {e}")

        if loaded > 0:
            logger.info(f"[TaskService] ✅ 已恢复 {loaded} 个自动封面定时任务")

    def add_task(
        self,
        task_id,
        cron_str,
        preset_filename,
        targets,
        mode,
        name="Unknown",
        fallback_to_next_backdrop=True,
    ):
        """添加新任务到调度器 (封面生成任务)"""
        try:
            # 定义调度器触发时要执行的包装函数
            def job_wrapper():
                # 调用上面的 execute_task_logic 函数
                execute_task_logic(
                    preset_filename=preset_filename,
                    targets=targets,
                    mode=mode,
                    task_name=name,
                    fallback_to_next_backdrop=fallback_to_next_backdrop,
                )

            # 添加任务到 APScheduler
            self.scheduler.add_job(
                job_wrapper,
                CronTrigger.from_crontab(cron_str),
                id=str(task_id),
                replace_existing=True
            )
            
            # 更新内存缓存 (用于 API 返回列表)
            self.active_tasks[str(task_id)] = {
                "id": task_id,
                "name": name,
                "cron": cron_str,
                "preset": preset_filename,
                "targets": targets,
                "mode": mode,
                "fallback_to_next_backdrop": fallback_to_next_backdrop,
                "enabled": True
            }
            
            logger.info(f"[TaskService] 任务添加成功: {name} - {cron_str}")
        except Exception as e:
            logger.error(f"[TaskService] 任务添加失败: {e}")
            traceback.print_exc()

    def remove_task(self, task_id):
        """删除任务"""
        try:
            self.scheduler.remove_job(str(task_id))
            if str(task_id) in self.active_tasks:
                del self.active_tasks[str(task_id)]
            logger.info(f"[TaskService] 任务删除成功: {task_id}")
        except Exception as e:
            logger.error(f"[TaskService] 删除任务时出错 {task_id}: {e}")

# ==========================================
# 3. 实例化对象 (供 main.py 导入)
# ==========================================
task_service_instance = TaskService()
