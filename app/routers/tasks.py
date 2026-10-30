# app/routers/tasks.py
import os
import json
import uuid
import threading
from fastapi import APIRouter, Body, HTTPException
from apscheduler.triggers.cron import CronTrigger

from app.schemas import CreateTaskRequest, UpdateTaskRequest, RunTaskRequest, RunSavedTaskRequest, ToggleTaskRequest
from app.dependencies import ACTIVE_TASKS, update_task_progress
from app.services.task_service import execute_task_logic, task_service_instance
from core.configs import TASKS_FILE, APP_LOG_FILE, TEMPLATES_DIR
from core.logger import logger

router = APIRouter(tags=["Tasks"])

# --- 辅助函数：添加任务到调度器 ---
def add_job_to_scheduler(task):
    try:
        cron_str = task.get("cron", "")
        if len(cron_str.split()) != 5: return
        # 使用 lambda 延迟绑定参数
        job_fn = lambda: execute_task_logic(
            task["preset"],
            task["targets"],
            task.get("mode", "random"),
            task["name"],
            task.get("fallback_to_next_backdrop", True),
        )
        task_service_instance.scheduler.add_job(job_fn, CronTrigger.from_crontab(cron_str), id=task["id"], name=task["name"], replace_existing=True)
        logger.info(f"[Scheduler] 已装载任务: {task['name']} ({cron_str})")
    except Exception as e:
        logger.error(f"[Scheduler] 装载任务失败 {task['name']}: {e}")

@router.get("/api/progress")
def get_progress(): 
    return ACTIVE_TASKS

@router.get("/api/system_logs")
def get_system_logs():
    logs = ""
    if os.path.exists(APP_LOG_FILE):
        try:
            with open(APP_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                logs = "".join(lines[-200:]) # 只返回最后200行
        except:
            logs = "Read logs failed."
    else:
        logs = "No log file found."
    return {"logs": logs}

@router.post("/api/clear_system_logs")
def clear_system_logs():
    """清空系统日志"""
    try:
        if os.path.exists(APP_LOG_FILE):
            with open(APP_LOG_FILE, "w", encoding="utf-8") as f:
                f.write("")
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/clear_task_progress")
def clear_task_progress(payload: dict = Body(...)):
    run_id = payload.get("run_id")
    if run_id in ACTIVE_TASKS: del ACTIVE_TASKS[run_id]
    return {"status": "ok"}

@router.post("/api/stop_task")
def stop_task(payload: dict = Body(...)):
    run_id = payload.get("run_id")
    if run_id in ACTIVE_TASKS: 
        ACTIVE_TASKS[run_id]['cancel_requested'] = True
    return {"status": "ok"}

@router.get("/api/tasks")
def get_tasks():
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f:
                return {"tasks": json.load(f)}
        except: pass
    return {"tasks": []}

@router.post("/api/run_task")
def run_task_batch(req: RunTaskRequest):
    # 手动批量运行（不保存）
    threading.Thread(
        target=execute_task_logic,
        args=(
            req.preset_filename,
            req.targets,
            req.mode,
            "Manual Batch",
            req.fallback_to_next_backdrop,
        ),
    ).start()
    return {"status": "ok", "message": "任务已在后台启动"}

@router.post("/api/run_saved_task")
def run_saved_task_endpoint(req: RunSavedTaskRequest):
    tasks = []
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f: tasks = json.load(f)
        except: pass
    
    target = next((t for t in tasks if t.get("id") == req.id), None)
    if not target: raise HTTPException(status_code=404, detail="Task not found")
    
    threading.Thread(
        target=execute_task_logic,
        args=(
            target["preset"],
            target["targets"],
            target.get("mode", "random"),
            target["name"],
            target.get("fallback_to_next_backdrop", True),
        ),
    ).start()
    return {"status": "ok", "message": "任务已在后台启动"}

@router.post("/api/create_task")
def create_task_endpoint(req: CreateTaskRequest):
    tasks = []
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f: tasks = json.load(f)
        except: pass
        
    task_id = str(uuid.uuid4())
    new_task = {
        "id": task_id, "name": req.name, "cron": req.cron,
        "preset": req.preset_filename, "targets": [t.model_dump() for t in req.targets], 
        "mode": req.mode,
        "fallback_to_next_backdrop": req.fallback_to_next_backdrop,
        "enabled": req.enabled
    }
    tasks.append(new_task)
    with open(TASKS_FILE, "w", encoding="utf-8") as f: 
        json.dump(tasks, f, indent=4, ensure_ascii=False)
    
    if req.enabled:
        add_job_to_scheduler(new_task)
    return {"status": "saved", "task_id": task_id}

@router.post("/api/update_task")
def update_task_endpoint(req: UpdateTaskRequest):
    tasks = []
    if os.path.exists(TASKS_FILE):
        try:
            with open(TASKS_FILE, "r", encoding="utf-8") as f: tasks = json.load(f)
        except: pass
        
    for i, t in enumerate(tasks):
        if t.get("id") == req.id:
            tasks[i] = {
                "id": req.id, "name": req.name, "cron": req.cron,
                "preset": req.preset_filename, "targets": [t.model_dump() for t in req.targets], 
                "mode": req.mode,
                "fallback_to_next_backdrop": req.fallback_to_next_backdrop,
                "enabled": req.enabled
            }
            with open(TASKS_FILE, "w", encoding="utf-8") as f: 
                json.dump(tasks, f, indent=4, ensure_ascii=False)
            
            # 更新调度器
            if task_service_instance.scheduler.get_job(req.id): task_service_instance.scheduler.remove_job(req.id)
            if req.enabled:
                add_job_to_scheduler(tasks[i])
            return {"status": "updated"}
            
    raise HTTPException(status_code=404, detail="Task not found")

@router.post("/api/delete_task")
def delete_task_endpoint(payload: dict = Body(...)):
    task_id = payload.get("id")
    if not os.path.exists(TASKS_FILE): return {"status": "ok"}
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f: tasks = json.load(f)
        tasks = [t for t in tasks if t.get("id") != task_id]
        with open(TASKS_FILE, "w", encoding="utf-8") as f: 
            json.dump(tasks, f, indent=4, ensure_ascii=False)
        if task_service_instance.scheduler.get_job(task_id): task_service_instance.scheduler.remove_job(task_id)
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/toggle_task")
def toggle_task_endpoint(req: ToggleTaskRequest):
    if not os.path.exists(TASKS_FILE): raise HTTPException(status_code=404)
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f: tasks = json.load(f)
        target = next((t for t in tasks if t.get("id") == req.id), None)
        if not target: raise HTTPException(status_code=404)
        
        target['enabled'] = req.enabled
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4, ensure_ascii=False)
            
        if req.enabled:
            add_job_to_scheduler(target)
        else:
            if task_service_instance.scheduler.get_job(req.id):
                task_service_instance.scheduler.remove_job(req.id)
                
        return {"status": "ok", "enabled": req.enabled}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
