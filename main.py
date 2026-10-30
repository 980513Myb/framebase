import uvicorn
import os
import shutil  # [新增] 用于文件复制
import asyncio
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from contextlib import asynccontextmanager

# 导入所有路由模块
from app.routers import auth
from app.routers import server
from app.routers import tasks
from app.routers import webhook
from app.routers import resources
from app.routers import wechat_notify
from app.routers import logs

# 导入核心组件
from core.logger import logger

# === 【核心修复点】路径修正：增加 app. 前缀 ===
from app.services.task_service import task_service_instance
# ============================================
import logging

APP_NAME = "FrameBase"
APP_VERSION = "1.0.4"

# ==========================================
# [新增] 日志屏蔽配置
# ==========================================
# 1. 屏蔽 httpx/httpcore 的 INFO 日志 (GET/POST 请求不打印)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# 2. [新增] 屏蔽 apscheduler 的英文启动日志
logging.getLogger("apscheduler").setLevel(logging.WARNING) 
# ==========================================


# ==========================================
# [新增] 启动时恢复默认文件逻辑
# ==========================================
def restore_defaults():
    """
    检查 config, fonts, templates 等目录。
    如果用户挂载了空卷导致文件缺失，从 defaults/ 目录恢复它们。
    """
    base_dir = os.getcwd()
    # 定义映射关系: 备份源 -> 目标目录
    # 注意：这些 defaults 目录是在 Dockerfile 构建阶段通过 cp 命令生成的
    folder_map = {
        "defaults/config": "config",
        "defaults/fonts": "fonts",
        "defaults/templates": "templates",
        "defaults/layouts": "layouts"
    }

    logger.info("[Init] 正在检查文件完整性。。。")

    for src_rel, dst_rel in folder_map.items():
        src_path = os.path.join(base_dir, src_rel)
        dst_path = os.path.join(base_dir, dst_rel)

        # 1. 如果镜像里本身就没有备份源，跳过
        if not os.path.exists(src_path):
            continue

        # 2. 确保目标根目录存在 (例如创建一个空的 /app/templates)
        if not os.path.exists(dst_path):
            try:
                os.makedirs(dst_path)
            except Exception:
                pass # 忽略已存在报错

        # 3. 递归遍历备份目录下的所有文件
        restore_count = 0
        for root, dirs, files in os.walk(src_path):
            # 计算相对路径，例如 fonts/myfont.ttf -> /myfont.ttf
            rel_path = os.path.relpath(root, src_path)
            target_root = os.path.join(dst_path, rel_path)

            if not os.path.exists(target_root):
                try:
                    os.makedirs(target_root)
                except Exception:
                    pass

            for file in files:
                src_file = os.path.join(root, file)
                dst_file = os.path.join(target_root, file)

                # 【核心逻辑】只有当目标文件不存在时才复制 
                # (既修复了空卷问题，又保护了用户修改过的文件不被覆盖)
                if not os.path.exists(dst_file):
                    try:
                        shutil.copy2(src_file, dst_file)
                        restore_count += 1
                    except Exception as e:
                        logger.error(f"[Init] 恢复文件失败 {dst_file}: {e}")
        
        if restore_count > 0:
            logger.info(f"[Init] 已从 {src_rel} 恢复了 {restore_count} 个文件到 {dst_rel}")


# ==========================================
# 1. 定义 UI 管理端 App (监听 5256)
# ==========================================

@asynccontextmanager
async def lifespan_ui(app: FastAPI):
    # --- 启动逻辑 ---
    logger.info("[System] 正在初始化系统组件...")
    try:
        # 尝试设置代理 (如果有)
        from core import tmdb
        from core.configs import global_config
        if global_config.proxy_url:
            tmdb.set_proxy(global_config.proxy_url)
            logger.info(f"[System] 已应用代理: {global_config.proxy_url}")
    except Exception as e:
        logger.warning(f"[System] 应用代理失败: {e}")

    # --- [修改] 启动调度器并手动打印中文日志 ---
    task_service_instance.scheduler.start()
    logger.info("[System] ✅ 定时任务调度器已启动")

    # [新增] 启动时恢复自动封面定时任务
    task_service_instance.load_active_jobs()
    logger.info("[System] ✅ 自动封面任务已加载")

    yield
    try:
        task_service_instance.scheduler.shutdown(wait=False)
    except Exception:
        pass
    logger.info("[System] 系统已关闭")

# 创建 UI 主应用
app = FastAPI(title=f"{APP_NAME} UI", version=APP_VERSION, lifespan=lifespan_ui)

# 允许跨域 (UI端)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载 API 路由 (只给 UI 用)
app.include_router(auth.router)
app.include_router(server.router)
app.include_router(tasks.router)
app.include_router(webhook.router)
app.include_router(resources.router)
app.include_router(wechat_notify.router)
app.include_router(logs.router)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/fonts", StaticFiles(directory="fonts"), name="fonts")
app.mount("/templates", StaticFiles(directory="templates"), name="templates")
app.mount("/backups", StaticFiles(directory="backups"), name="backups")

@app.get("/")
async def root():
    return RedirectResponse(url="/static/index.html", status_code=302)

@app.get("/api/health")
async def health():
    return {"status": "ok", "app": APP_NAME, "version": APP_VERSION}


# ==========================================
# 2. 启动器
# ==========================================

async def serve_apps():
    """启动 FrameBase 管理服务。"""

    logger.info(f">>> [BOOT] UI 服务启动端口: 5256")

    config_ui = uvicorn.Config(
        app,
        host="0.0.0.0",
        port=5256,
        log_level="warning"
    )

    server_ui = uvicorn.Server(config_ui)

    try:
        await server_ui.serve()
    except asyncio.CancelledError:
        # 捕获任务取消信号，防止控制台打印一大堆 Traceback
        pass

if __name__ == "__main__":
    # --- [Step 1] 优先执行默认文件恢复 ---
    # 这必须在任何其他操作之前，确保 fonts/templates 等文件就位
    restore_defaults()

    # --- [Step 2] 检查必要目录 (保留原逻辑作为双重保险) ---
    if not os.path.exists("fonts"):
        os.makedirs("fonts")
        logger.info("创建 fonts 目录")
    
    logger.info(f">>> [BOOT] 程序所在根目录: {os.getcwd()}")
    logger.info(">>> 正在启动 FrameBase 服务...")
    logger.info("    - 访问管理后台: http://localhost:5256/static/index.html")

    # 运行异步主程序
    try:
        asyncio.run(serve_apps())
    except KeyboardInterrupt:
        # 捕获最外层的 Ctrl+C，打印一句简单的提示即可
        logger.warning(">>> 服务已停止 (User Stopped)")
    except Exception as e:
        logger.error(f"非正常退出: {e}")
        
