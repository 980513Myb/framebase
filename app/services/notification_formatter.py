# app/services/notification_formatter.py
import copy
from jinja2 import Template

# 通知模板默认值
DEFAULT_TEMPLATES = {
    "media_added": {
        "title": "《{{ title }}》{% if year %}({{ year }}){% endif %} 已入库 ✅",
        "text": "⭐️评分：{{ rating or '暂无' }} ｜ 🎬类型：{{ media_type }}{% if genres %} · {{ genres }}{% endif %}"
                "{% if tagline %}\n💬标语：{{ tagline }}{% endif %}"
                "\n\n📝简介：{{ overview or '暂无简介' }}"
                "\n\n📁媒体库：{{ library_name }} ｜ 🕐入库时间：{{ now }}"
    },
    "playback": {
        "title": "🎬 正在播放《{{ title }}》",
        "text": "👤播放用户：{{ user_name or '未知' }} ｜ 📺设备：{{ device_name or '未知' }}"
                "\n📱客户端：{{ client_name or client_info or '未知' }} ｜ 🌐IP：{{ device_ip or '未知' }}"
                "\n🖥️服务器：{{ emby_name }} ｜ 🕐时间：{{ now }}"
                "\n\n⭐️评分：{{ rating or '暂无' }} ｜ 🎬类型：{{ media_type }}{% if genres %} · {{ genres }}{% endif %}"
                "{% if tagline %}\n💬标语：{{ tagline }}{% endif %}"
                "\n\n📝简介：{{ overview or '暂无简介' }}"
    }
}


def render_template(template_str: str, context: dict) -> str:
    """渲染 Jinja2 模板，失败时返回原始字符串"""
    if not template_str:
        return ""
    try:
        tpl = Template(template_str)
        return tpl.render(**context)
    except Exception as e:
        from core.logger import logger
        logger.error(f"[Formatter] 模板渲染失败: {e} | 模板: {template_str[:80]}")
        return template_str


def get_default_templates() -> dict:
    """返回默认模板的深拷贝"""
    return copy.deepcopy(DEFAULT_TEMPLATES)


def merge_templates(user_templates: dict) -> dict:
    """用用户自定义模板覆盖默认模板，缺失项保留默认"""
    defaults = get_default_templates()
    if not user_templates:
        return defaults
    for notify_type, templates in user_templates.items():
        if notify_type in defaults and isinstance(templates, dict):
            for key in ["title", "text"]:
                if key in templates and templates[key]:
                    defaults[notify_type][key] = templates[key]
    return defaults
