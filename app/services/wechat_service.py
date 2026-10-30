# app/services/wechat_service.py
import os
import json
import hashlib
import html
import requests
from datetime import datetime
from typing import Optional, List, Dict, Any
from core.configs import WECHAT_NOTIFY_CONFIG_FILE
from core.logger import logger
from app.services.notification_formatter import render_template, merge_templates


# TMDB 图片基础 URL
TMDB_IMAGE_BASE_URL = "https://image.tmdb.org/t/p/w500"

# 通知类型定义
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


class WechatNotifyService:
    """企业微信通知服务 - 支持图文消息"""

    def __init__(self):
        self.config = self._load_config()
        self._access_token = None
        self._token_expires = 0
        self._token_acquired_time = 0  # 记录token获取时间

    def _load_config(self) -> dict:
        """加载配置"""
        config = None
        if os.path.exists(WECHAT_NOTIFY_CONFIG_FILE):
            try:
                with open(WECHAT_NOTIFY_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except Exception as e:
                logger.error(f"[WechatNotify] 加载配置失败: {e}")
        if config is None:
            config = {
                "enabled": False,
                "name": "企微",
                "channel_name": "",
                "corp_id": "",
                "app_secret": "",
                "token": "",
                "agent_id": "",
                "proxy_url": "",
                "encoding_aes_key": "",
                "admin_whitelist": "",
                "notify_types": {
                    "playback": True,
                    "media_added": True,
                    "task_complete": True
                }
            }
        # 合并通知模板
        defaults = {
            key: True
            for key in NOTIFICATION_TYPES
        }
        incoming_types = config.get("notify_types") or {}
        config["notify_types"] = {
            key: incoming_types.get(key, default)
            for key, default in defaults.items()
        }
        if config.get("name") in ("微信", "企业微信"):
            config["name"] = "企微"
        config["templates"] = merge_templates(config.get("templates"))
        return config

    def _save_config(self):
        """保存配置"""
        try:
            with open(WECHAT_NOTIFY_CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"[WechatNotify] 保存配置失败: {e}")

    def update_config(self, new_config: dict):
        """更新配置"""
        incoming_types = new_config.get("notify_types") or {}
        new_config["notify_types"] = {
            key: incoming_types.get(key, True)
            for key in NOTIFICATION_TYPES
        }
        # 合并通知模板，防止前端未传 templates 时丢失默认模板
        new_config["templates"] = merge_templates(new_config.get("templates"))
        self.config = new_config
        self._save_config()
        # 清除缓存的token
        self._access_token = None
        self._token_expires = 0

    def get_config(self) -> dict:
        """获取配置"""
        return self.config

    def _get_api_base_url(self) -> str:
        """获取 API 基础 URL（支持代理）"""
        proxy_url = self.config.get("proxy_url", "").strip()
        if proxy_url:
            # 2022年6月后创建的应用需要使用代理URL作为基础URL
            return proxy_url.rstrip("/")
        return "https://qyapi.weixin.qq.com"

    def _get_access_token(self, force: bool = False) -> Optional[str]:
        """获取企业微信 access_token"""
        import time

        if not self.config.get("corp_id") or not self.config.get("app_secret"):
            logger.error("[WechatNotify] 缺少 corp_id 或 app_secret")
            return None

        # 检查是否需要刷新token（提前5分钟刷新）
        current_time = time.time()
        if not force and self._access_token and current_time < self._token_acquired_time + self._token_expires - 300:
            return self._access_token

        base_url = self._get_api_base_url()
        url = f"{base_url}/cgi-bin/gettoken"
        params = {
            "corpid": self.config["corp_id"],
            "corpsecret": self.config["app_secret"]
        }

        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            if data.get("errcode") == 0:
                self._access_token = data["access_token"]
                self._token_expires = data.get("expires_in", 7200)
                self._token_acquired_time = current_time
                logger.info("[WechatNotify] access_token 获取成功")
                return self._access_token
            else:
                logger.error(f"[WechatNotify] 获取 access_token 失败: {data}")
                return None
        except Exception as e:
            logger.error(f"[WechatNotify] 获取 access_token 异常: {e}")
            return None

    def _send_request(self, url: str, payload: dict, _retried: bool = False) -> bool:
        """发送请求到企业微信API"""
        try:
            resp = requests.post(
                url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            data = resp.json()
            if data.get("errcode") == 0:
                return True
            elif data.get("errcode") == 42001 and not _retried:
                # Token过期，强制刷新后重试（仅重试一次）
                logger.warning("[WechatNotify] access_token 已过期，正在刷新...")
                if self._get_access_token(force=True):
                    base_url = self._get_api_base_url()
                    new_url = f"{base_url}/cgi-bin/message/send?access_token={self._access_token}"
                    return self._send_request(new_url, payload, _retried=True)
                return False
            else:
                logger.error(f"[WechatNotify] 消息发送失败: {data}")
                return False
        except Exception as e:
            logger.error(f"[WechatNotify] 消息发送异常: {e}")
            return False

    def _upload_image_media(self, image_data: bytes, content_type: str = "image/jpeg",
                            _retried: bool = False) -> Optional[str]:
        """Upload an image so WeCom can render private/LAN Emby posters."""
        if not image_data:
            return None
        access_token = self._get_access_token(force=_retried)
        if not access_token:
            return None

        extension = "png" if content_type == "image/png" else "webp" if content_type == "image/webp" else "jpg"
        base_url = self._get_api_base_url()
        url = f"{base_url}/cgi-bin/media/upload?access_token={access_token}&type=image"
        try:
            response = requests.post(
                url,
                files={"media": (f"poster.{extension}", image_data, content_type)},
                timeout=20,
            )
            data = response.json()
            if data.get("errcode") == 0 and data.get("media_id"):
                logger.info("[WechatNotify] 海报素材上传成功")
                return data["media_id"]
            if data.get("errcode") == 42001 and not _retried:
                return self._upload_image_media(image_data, content_type, _retried=True)
            logger.error(f"[WechatNotify] 海报素材上传失败: {data}")
        except Exception as exc:
            logger.error(f"[WechatNotify] 海报素材上传异常: {exc}")
        return None

    def _send_mpnews_message(self, title: str, description: str, image_data: bytes,
                             content_type: str = "image/jpeg", link_url: str = "",
                             to_user: str = "@all") -> bool:
        media_id = self._upload_image_media(image_data, content_type)
        if not media_id:
            return False

        content = html.escape(description or "").replace("\n", "<br>")
        payload = {
            "touser": to_user,
            "msgtype": "mpnews",
            "agentid": self.config.get("agent_id", ""),
            "mpnews": {
                "articles": [{
                    "title": title,
                    "thumb_media_id": media_id,
                    "author": "FrameBase",
                    "content_source_url": link_url,
                    "content": f"<div>{content}</div>",
                    "digest": (description or "")[:240],
                }]
            },
            "safe": 0,
        }
        access_token = self._get_access_token()
        if not access_token:
            return False
        url = f"{self._get_api_base_url()}/cgi-bin/message/send?access_token={access_token}"
        if self._send_request(url, payload):
            logger.info(f"[WechatNotify] 带海报图文消息发送成功: {title}")
            return True
        return False

    def send_message(self, content: str, to_user: str = "@all") -> bool:
        """
        发送文本消息

        Args:
            content: 消息内容
            to_user: 接收用户，默认 @all 发送给所有人

        Returns:
            bool: 是否发送成功
        """
        if not self.config.get("enabled"):
            logger.warning("[WechatNotify] 通知未启用")
            return False

        access_token = self._get_access_token()
        if not access_token:
            return False

        base_url = self._get_api_base_url()
        url = f"{base_url}/cgi-bin/message/send?access_token={access_token}"

        payload = {
            "touser": to_user,
            "msgtype": "text",
            "agentid": self.config.get("agent_id", ""),
            "text": {
                "content": content
            },
            "safe": 0,
            "enable_id_trans": 0,
            "enable_duplicate_check": 0
        }

        if self._send_request(url, payload):
            logger.info(f"[WechatNotify] 消息发送成功: {content[:50]}...")
            return True
        return False

    def send_markdown(self, content: str, to_user: str = "@all") -> bool:
        """
        发送 Markdown 消息

        Args:
            content: Markdown 内容
            to_user: 接收用户

        Returns:
            bool: 是否发送成功
        """
        if not self.config.get("enabled"):
            logger.warning("[WechatNotify] 通知未启用")
            return False

        access_token = self._get_access_token()
        if not access_token:
            return False

        base_url = self._get_api_base_url()
        url = f"{base_url}/cgi-bin/message/send?access_token={access_token}"

        payload = {
            "touser": to_user,
            "msgtype": "markdown",
            "agentid": self.config.get("agent_id", ""),
            "markdown": {
                "content": content
            }
        }

        if self._send_request(url, payload):
            logger.info("[WechatNotify] Markdown消息发送成功")
            return True
        return False

    def send_news_message(self, title: str, description: str, image_url: str = "",
                          link_url: str = "", to_user: str = "@all",
                          image_data: bytes = None, image_content_type: str = "image/jpeg") -> bool:
        """
        发送图文消息（卡片样式）

        Args:
            title: 卡片标题
            description: 卡片描述
            image_url: 图片地址（海报/背景图）
            link_url: 点击跳转链接
            to_user: 接收用户

        Returns:
            bool: 是否发送成功
        """
        if not self.config.get("enabled"):
            logger.warning("[WechatNotify] 通知未启用")
            return False

        if image_data and self._send_mpnews_message(
            title,
            description,
            image_data,
            image_content_type,
            link_url,
            to_user,
        ):
            return True

        access_token = self._get_access_token()
        if not access_token:
            return False

        base_url = self._get_api_base_url()
        url = f"{base_url}/cgi-bin/message/send?access_token={access_token}"

        article = {
            "title": title,
            "description": description,
            "picurl": image_url,
            "url": link_url
        }

        payload = {
            "touser": to_user,
            "msgtype": "news",
            "agentid": self.config.get("agent_id", ""),
            "news": {
                "articles": [article]
            }
        }

        if self._send_request(url, payload):
            logger.info(f"[WechatNotify] 图文消息发送成功: {title}")
            return True
        return False

    def send_news_messages(self, articles: List[Dict[str, str]], to_user: str = "@all") -> bool:
        """
        发送多条图文消息

        Args:
            articles: 文章列表，每篇文章包含 title, description, picurl, url
            to_user: 接收用户

        Returns:
            bool: 是否发送成功
        """
        if not self.config.get("enabled"):
            logger.warning("[WechatNotify] 通知未启用")
            return False

        if not articles:
            logger.warning("[WechatNotify] 文章列表为空")
            return False

        access_token = self._get_access_token()
        if not access_token:
            return False

        base_url = self._get_api_base_url()
        url = f"{base_url}/cgi-bin/message/send?access_token={access_token}"

        # 最多支持8条图文
        articles = articles[:8]

        payload = {
            "touser": to_user,
            "msgtype": "news",
            "agentid": self.config.get("agent_id", ""),
            "news": {
                "articles": articles
            }
        }

        if self._send_request(url, payload):
            logger.info(f"[WechatNotify] 多图文消息发送成功: {len(articles)}条")
            return True
        return False

    def send_task_notification(self, task_name: str, status: str, message: str = "") -> bool:
        """
        发送任务完成通知

        Args:
            task_name: 任务名称
            status: 任务状态 (success/failed)
            message: 附加消息

        Returns:
            bool: 是否发送成功
        """
        status_emoji = "✅" if status == "success" else "❌"
        status_text = "成功" if status == "success" else "失败"

        content = f"""## {status_emoji} 海报通知

**任务名称**: {task_name}
**状态**: {status_text}
"""
        if message:
            content += f"\n**详情**: {message}\n"

        content += f"\n> 来自 FrameBase"

        return self.send_markdown(content)

    def test_connection(self) -> dict:
        """测试连接"""
        result = {"success": False, "message": ""}

        if not self.config.get("corp_id"):
            result["message"] = "缺少企业ID"
            return result

        if not self.config.get("app_secret"):
            result["message"] = "缺少应用Secret"
            return result

        if not self.config.get("agent_id"):
            result["message"] = "缺少应用AgentId"
            return result

        access_token = self._get_access_token(force=True)
        if access_token:
            result["success"] = True
            base_url = self._get_api_base_url()
            proxy_info = f" (代理: {base_url})" if base_url != "https://qyapi.weixin.qq.com" else ""
            result["message"] = f"连接成功，access_token 获取正常{proxy_info}"
        else:
            result["message"] = "获取 access_token 失败，请检查配置"

        return result

    def is_notify_type_enabled(self, notify_type: str) -> bool:
        """检查特定类型的通知是否启用"""
        if not self.config.get("enabled"):
            return False
        notify_types = self.config.get("notify_types", {})
        return notify_types.get(notify_type, False)

    def _get_media_poster_url(self, media_name: str, media_type: str = "movie",
                               year: str = "", tmdb_id: str = "") -> str:
        """
        获取媒体海报图片URL

        Args:
            media_name: 媒体名称
            media_type: 媒体类型 (movie/tv)
            year: 年份
            tmdb_id: TMDB ID（如果有）

        Returns:
            str: 海报图片URL，获取失败返回空字符串
        """
        try:
            # 尝试从配置中获取 TMDB API Key
            import config_manager
            import constants
            api_key = config_manager.APP_CONFIG.get(constants.CONFIG_OPTION_TMDB_API_KEY)

            if not api_key:
                logger.debug("[WechatNotify] 未配置 TMDB API Key，无法获取海报")
                return ""

            # 如果有 tmdb_id，直接获取详情
            if tmdb_id:
                try:
                    from core import tmdb as tmdb_module
                    if media_type == "movie":
                        details = tmdb_module.get_movie_details(int(tmdb_id), api_key, append_to_response=None)
                    else:
                        details = tmdb_module.get_tv_details(int(tmdb_id), api_key, append_to_response=None)

                    if details:
                        poster_path = details.get("poster_path")
                        if poster_path:
                            return f"{TMDB_IMAGE_BASE_URL}{poster_path}"
                except Exception as e:
                    logger.debug(f"[WechatNotify] 通过 TMDB ID 获取海报失败: {e}")

            # 否则搜索媒体
            from core import tmdb as tmdb_module
            results = tmdb_module.search_media(media_name, api_key, item_type=media_type, year=year)

            if results and len(results) > 0:
                poster_path = results[0].get("poster_path")
                if poster_path:
                    return f"{TMDB_IMAGE_BASE_URL}{poster_path}"

        except Exception as e:
            logger.debug(f"[WechatNotify] 获取海报失败: {e}")

        return ""

    def notify_playback(self, item_name: str, emby_name: str = "Emby",
                        user_agent: str = "", poster_url: str = "",
                        original_name: str = "", media_type: str = "movie",
                        overview: str = "", rating: str = "", genres: str = "",
                        tagline: str = "", user_name: str = "",
                        client_info: str = "", client_name: str = "",
                        device_name: str = "", device_ip: str = "",
                        poster_data: bytes = None,
                        poster_content_type: str = "image/jpeg", **kwargs) -> bool:
        """
        发送播放通知（图文卡片样式）
        """
        if not self.is_notify_type_enabled("playback"):
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 用模板渲染标题和正文
        templates = self.config.get("templates", {}).get("playback", {})
        title_tpl = templates.get("title", "🎬 正在播放《{{ title }}》")
        text_tpl = templates.get("text", "")

        context = {
            "title": item_name,
            "media_type": "电影" if media_type == "movie" else "剧集",
            "rating": rating or "",
            "genres": genres or "",
            "overview": overview or "",
            "tagline": tagline or "",
            "emby_name": emby_name,
            "client_info": client_info or "未知客户端",
            "client_name": client_name or "",
            "device_name": device_name or "",
            "device_ip": device_ip or "",
            "user_name": user_name or "未知用户",
            "now": now,
            "poster_url": poster_url or "",
        }

        title = render_template(title_tpl, context)
        description = render_template(text_tpl, context)

        # 海报优先用传入的，如果为空或是内网地址则从 TMDB 获取
        search_name = original_name or item_name.replace("🎬 ", "").replace("📺 ", "").split(" S")[0]
        if not poster_data and (not poster_url or poster_url.startswith("http://")):
            poster_url = self._get_media_poster_url(search_name, media_type)

        return self.send_news_message(
            title=title,
            description=description,
            image_url=poster_url,
            image_data=poster_data,
            image_content_type=poster_content_type or "image/jpeg",
        )

    def notify_media_added(self, media_name: str, media_type: str = "movie",
                           library_name: str = "", year: str = "",
                           poster_url: str = "", tmdb_id: str = "",
                           original_name: str = "",
                           overview: str = "", rating: str = "", genres: str = "",
                           tagline: str = "", **kwargs) -> bool:
        """
        发送新媒体入库通知（图文卡片样式）
        """
        if not self.is_notify_type_enabled("media_added"):
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 用模板渲染标题和正文
        templates = self.config.get("templates", {}).get("media_added", {})
        title_tpl = templates.get("title", "《{{ title }}》{% if year %}({{ year }}){% endif %} 已入库 ✅")
        text_tpl = templates.get("text", "")

        context = {
            "title": media_name,
            "year": str(year) if year else "",
            "media_type": "电影" if media_type == "movie" else "剧集",
            "library_name": library_name,
            "rating": rating or "",
            "genres": genres or "",
            "overview": overview or "",
            "tagline": tagline or "",
            "poster_url": poster_url or "",
            "now": now,
        }

        title = render_template(title_tpl, context)
        description = render_template(text_tpl, context)

        # 如果没有提供海报，尝试从 TMDB 获取
        if not poster_url:
            search_name = original_name or media_name.split(" S")[0]
            poster_url = self._get_media_poster_url(search_name, media_type, year, tmdb_id)

        return self.send_news_message(
            title=title,
            description=description,
            image_url=poster_url
        )

    def notify_task_complete(self, task_name: str, status: str = "success",
                             detail: str = "", posters_count: int = 0,
                             poster_url: str = "") -> bool:
        """
        发送任务完成通知（图文卡片样式）

        Args:
            task_name: 任务名称
            status: 任务状态 (success/failed)
            detail: 详细信息
            posters_count: 处理的海报数量
            poster_url: 海报图片URL（可选，显示生成的海报）

        Returns:
            bool: 是否发送成功
        """
        if not self.is_notify_type_enabled("task_complete"):
            return False

        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if status == "success":
            status_emoji = "✅"
            status_text = "执行成功"
        else:
            status_emoji = "❌"
            status_text = "执行失败"

        # 构建卡片标题和描述
        title = f"{status_emoji} {task_name}"
        description = f"""状态：{status_text}"""
        if posters_count > 0:
            description += f"\n处理数量：{posters_count} 张海报"
        if detail:
            description += f"\n详情：{detail}"
        description += f"\n时间：{now}"
        description += "\n\n— FrameBase"

        return self.send_news_message(
            title=title,
            description=description,
            image_url=poster_url
        )


# 全局实例
wechat_notify_service = WechatNotifyService()
