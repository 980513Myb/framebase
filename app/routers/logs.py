from fastapi import APIRouter, HTTPException, Query

from app.services.log_service import summarize_log_file
from core.configs import APP_LOG_FILE


router = APIRouter(tags=["Logs"])


@router.get("/api/logs/summary")
def get_log_summary(
    limit: int = Query(default=250, ge=1, le=2000),
    category: str = Query(default="all"),
    level: str = Query(default="all"),
    hours: int = Query(default=0, ge=0, le=720),
):
    try:
        return summarize_log_file(
            APP_LOG_FILE,
            limit=limit,
            category=category,
            level=level,
            hours=hours,
        )
    except OSError as exc:
        raise HTTPException(status_code=500, detail=f"读取日志失败: {exc}") from exc
