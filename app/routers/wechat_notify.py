# app/routers/wechat_notify.py
import hashlib
import xml.etree.ElementTree as ET
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import PlainTextResponse

from app.schemas import WechatNotifyConfigModel
from app.services.wechat_service import wechat_notify_service, NOTIFICATION_TYPES as WECHAT_NOTIFICATION_TYPES
from core.logger import logger

router = APIRouter(tags=["Notify"])


# ==========================================
# 通知类型（通用）
# ==========================================
NOTIFICATION_TYPES = {
    "playback": {
        "name": "播放通知",
        "description": "有人播放媒体时发送通知",
        "icon": "🎬"
    },
    "media_added": {
        "name": "入库通知",
        "description": "新媒体添加到媒体库时发送通知",
        "icon": "📚"
    },
    "task_complete": {
        "name": "海报通知",
        "description": "海报生成等任务完成时发送通知",
        "icon": "🎨"
    }
}


# ==========================================
# 通用接口
# ==========================================

@router.get("/api/notify/types")
def get_notification_types():
    """获取可用的通知类型列表"""
    return NOTIFICATION_TYPES


@router.get("/api/notify/channels")
def get_notification_channels():
    """获取企业微信通知状态。"""
    config = wechat_notify_service.get_config()
    return {
        "wechat": {
            "name": "企业微信",
            "enabled": config.get("enabled", False),
            "configured": bool(config.get("corp_id") and config.get("app_secret")),
        }
    }


# ==========================================
# 企业微信接口
# ==========================================

@router.get("/api/wechat-notify/types")
def get_wechat_notification_types():
    """获取可用的通知类型列表（兼容旧接口）"""
    return NOTIFICATION_TYPES


@router.get("/api/wechat-notify/config")
def get_wechat_notify_config():
    """获取企微通知配置"""
    return wechat_notify_service.get_config()


@router.post("/api/wechat-notify/config")
def save_wechat_notify_config(cfg: WechatNotifyConfigModel):
    """保存企微通知配置"""
    try:
        wechat_notify_service.update_config(cfg.model_dump())
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/wechat-notify/test")
def test_wechat_notify():
    """测试微信通知连接"""
    result = wechat_notify_service.test_connection()
    if result["success"]:
        return {"status": "ok", "message": result["message"]}
    else:
        return {"status": "error", "message": result["message"]}


@router.post("/api/wechat-notify/send")
def send_wechat_test_message(message: str = "这是一条测试消息"):
    """发送测试消息"""
    success = wechat_notify_service.send_message(message)
    if success:
        return {"status": "ok", "message": "消息发送成功"}
    else:
        return {"status": "error", "message": "消息发送失败"}


@router.post("/api/wechat-notify/test-template")
def test_wechat_template():
    """用当前模板发送测试通知"""
    # 先保存配置（确保模板已持久化）
    # 然后调用 notify_playback 发送一条模板渲染后的测试通知
    success = wechat_notify_service.notify_playback(
        item_name="🎬 测试电影 (2026)",
        emby_name="FrameBase",
        user_agent="Mozilla/5.0 Test",
        poster_url="",
        original_name="Test Movie",
        media_type="movie",
        overview="这是一条测试通知，用于预览模板效果。如果你看到这条消息，说明模板渲染和通知发送都正常工作。",
        rating="8.5",
        genres="科幻, 动作, 冒险",
        tagline="测试标语 - 模板效果预览",
    )
    if success:
        return {"status": "ok", "message": "模板测试通知发送成功"}
    else:
        return {"status": "error", "message": "模板测试通知发送失败，请检查通知是否启用"}


@router.get("/api/wechat-notify/callback")
async def wechat_callback_verify(
    msg_signature: str = "",
    timestamp: str = "",
    nonce: str = "",
    echostr: str = ""
):
    """
    企业微信回调 URL 验证
    企业微信会发送 GET 请求来验证 URL 有效性
    """
    config = wechat_notify_service.get_config()
    token = config.get("token", "")

    if not token:
        return PlainTextResponse("token not configured", status_code=400)

    # 验证签名
    sort_list = [token, timestamp, nonce, echostr]
    sort_list.sort()
    sha = hashlib.sha1()
    sha.update("".join(sort_list).encode())
    signature = sha.hexdigest()

    if signature == msg_signature:
        # 解密 echostr（如果配置了 EncodingAESKey）
        encoding_aes_key = config.get("encoding_aes_key", "")
        if encoding_aes_key:
            # 使用企业微信的加密消息解密
            from app.services.wechat_crypto import WeChatCrypto
            try:
                crypto = WeChatCrypto(token, encoding_aes_key, config.get("corp_id", ""))
                echo_str = crypto.decrypt(echostr, msg_signature, timestamp, nonce)
                return PlainTextResponse(echo_str)
            except Exception:
                # 解密失败，直接返回 echostr
                return PlainTextResponse(echostr)
        else:
            return PlainTextResponse(echostr)
    else:
        return PlainTextResponse("invalid signature", status_code=403)


@router.post("/api/wechat-notify/callback")
async def wechat_callback_message(request: Request):
    """
    接收企业微信推送的消息。
    FrameBase 当前仅保留通知通道连通性，不从文本回调触发业务任务。
    """
    try:
        body = await request.body()
        if not body:
            return PlainTextResponse("success")

        config = wechat_notify_service.get_config()
        encoding_aes_key = config.get("encoding_aes_key", "")
        token = config.get("token", "")
        corp_id = config.get("corp_id", "")

        # 解析 XML
        try:
            root = ET.fromstring(body)
        except ET.ParseError:
            return PlainTextResponse("success")

        xml_content = body

        # 如果配置了加密，需要解密
        if encoding_aes_key and token:
            encrypt_elem = root.find("Encrypt")
            if encrypt_elem is not None and encrypt_elem.text:
                try:
                    from app.services.wechat_crypto import WeChatCrypto
                    # 获取签名参数（从 query string）
                    msg_signature = request.query_params.get("msg_signature", "")
                    timestamp = request.query_params.get("timestamp", "")
                    nonce = request.query_params.get("nonce", "")
                    crypto = WeChatCrypto(token, encoding_aes_key, corp_id)
                    decrypted = crypto.decrypt(encrypt_elem.text, msg_signature, timestamp, nonce)
                    xml_content = decrypted
                    root = ET.fromstring(xml_content)
                except Exception as e:
                    logger.error(f"[WeChat] 消息解密失败: {e}")
                    return PlainTextResponse("success")

        # 提取消息内容
        msg_type = root.findtext("MsgType", "")
        if msg_type != "text":
            return PlainTextResponse("success")

        content = root.findtext("Content", "")
        if not content:
            return PlainTextResponse("success")
        logger.info("[WeChat] 收到文本回调，当前仅保留通知通道连通性")

    except Exception as e:
        logger.error(f"[WeChat] 处理回调消息异常: {e}")

    return PlainTextResponse("success")


def send_to_all_channels(title: str, description: str, image_url: str = "",
                         notify_type: str = None):
    """发送企业微信图文通知。"""
    wechat_enabled = wechat_notify_service.is_notify_type_enabled(notify_type) if notify_type else wechat_notify_service.get_config().get("enabled")
    if wechat_enabled:
        return {"wechat": wechat_notify_service.send_news_message(
            title=title,
            description=description,
            image_url=image_url
        )}
    return {"wechat": None}
