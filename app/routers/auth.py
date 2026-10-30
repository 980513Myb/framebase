# app/routers/auth.py
import time
import uuid
import json
import os
from fastapi import APIRouter, Header, HTTPException
from app.schemas import LoginRequest, ChangeAuthRequest
from core.configs import AUTH_FILE

router = APIRouter(tags=["Auth"])

SESSION_TTL_SECONDS = 24 * 60 * 60
_active_sessions: dict[str, dict] = {}

def get_auth_creds():
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {
        "username": "admin",
        "password": "password"
    }

def _purge_expired_sessions():
    now = time.time()
    expired = [token for token, item in _active_sessions.items() if item.get("expires_at", 0) <= now]
    for token in expired:
        _active_sessions.pop(token, None)

def _issue_session(username: str) -> str:
    _purge_expired_sessions()
    token = str(uuid.uuid4())
    _active_sessions[token] = {
        "username": username,
        "expires_at": time.time() + SESSION_TTL_SECONDS,
    }
    return token

def verify_api_token(
    authorization: str | None = Header(default=None, alias="Authorization"),
    x_alsemby_token: str | None = Header(default=None, alias="X-ALSEMBY-Token"),
):
    _purge_expired_sessions()
    token = x_alsemby_token or ""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token or token not in _active_sessions:
        raise HTTPException(status_code=401, detail="登录已失效，请重新登录")
    return _active_sessions[token]["username"]

@router.post("/api/login")
def login(req: LoginRequest):
    creds = get_auth_creds()
    if req.username == creds.get("username") and req.password == creds.get("password"):
        return {"status": "ok", "token": _issue_session(req.username), "username": req.username}
    raise HTTPException(status_code=401, detail="Error")

@router.post("/api/change_auth")
def change_auth(req: ChangeAuthRequest):
    creds = get_auth_creds()
    if req.old_password != creds.get("password"): 
        raise HTTPException(status_code=401, detail="Old password incorrect")
    try:
        with open(AUTH_FILE, "w", encoding="utf-8") as f:
            json.dump({"username": req.new_username, "password": req.new_password}, f)
        _active_sessions.clear()
        return {"status": "ok"}
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/user_info")
def get_user_info():
    creds = get_auth_creds()
    return {"username": creds.get("username", "admin")}
