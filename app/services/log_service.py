import os
import re
from collections import Counter
from datetime import datetime, timedelta


LOG_LEVELS = ("TRACE", "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
DISPLAY_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR")
TIMESTAMP_FORMATS = ("%Y-%m-%d %H:%M:%S,%f", "%Y-%m-%d %H:%M:%S")


def _parse_timestamp(value):
    for fmt in TIMESTAMP_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    return None


def _classify_log(logger_name, message):
    text = f"{logger_name} {message}".lower()
    if "webhook" in text:
        return "webhook"
    if any(token in text for token in ("notify", "wechat", "wecom", "企微", "通知")):
        return "notify"
    if any(token in text for token in ("embyclient", "[emby]", " emby ", "/emby/", "媒体库连接")):
        return "emby"
    if any(token in text for token in (
        "[cover]", "[engine]", "[task", "poster", "封面", "布局", "gif ", "apng",
    )):
        return "cover"
    return "system"


def _parse_log_line(raw, entry_id):
    line = raw.rstrip("\r\n")
    parts = line.split(" - ")
    timestamp_text = ""
    parsed_time = None
    logger_name = ""
    level = "INFO"
    message = line.strip()

    if parts:
        candidate_time = _parse_timestamp(parts[0].strip())
        if candidate_time is not None:
            parsed_time = candidate_time
            timestamp_text = parts[0].strip()
            level_index = next(
                (index for index in range(1, len(parts)) if parts[index].strip().upper() in LOG_LEVELS),
                None,
            )
            if level_index is not None:
                level = parts[level_index].strip().upper()
                logger_name = " - ".join(parts[1:level_index]).strip()
                message = " - ".join(parts[level_index + 1:]).strip()

    if level == "TRACE":
        level = "DEBUG"
    elif level == "CRITICAL":
        level = "ERROR"

    category = _classify_log(logger_name, message)
    return {
        "id": entry_id,
        "time": parsed_time.strftime("%H:%M:%S") if parsed_time else "",
        "timestamp": timestamp_text,
        "level": level,
        "category": category,
        "logger": logger_name,
        "message": message,
        "raw": line,
        "_datetime": parsed_time,
    }


def _issue_signature(message):
    signature = message.lower()
    signature = re.sub(r"[0-9a-f]{12,}", "<id>", signature)
    signature = re.sub(r"\b\d+(?:\.\d+)?\b", "#", signature)
    signature = re.sub(r"\s+", " ", signature).strip()
    return signature[:180]


def _build_hotspots(entries):
    issue_entries = [entry for entry in entries if entry["level"] in ("WARNING", "ERROR")]
    counts = Counter((entry["level"], entry["category"], _issue_signature(entry["message"])) for entry in issue_entries)
    hotspots = []
    for (level, category, signature), count in counts.most_common(8):
        matches = [
            entry for entry in issue_entries
            if entry["level"] == level
            and entry["category"] == category
            and _issue_signature(entry["message"]) == signature
        ]
        latest = matches[-1]
        hotspots.append({
            "level": level,
            "category": category,
            "signature": signature,
            "count": count,
            "sample": latest["message"],
            "last_time": latest["time"],
        })
    return hotspots


def _build_explanations(entries):
    issues = [entry["message"].lower() for entry in entries if entry["level"] in ("WARNING", "ERROR")]
    rules = (
        ("connection", ("connection", "connect", "timeout", "连接", "超时"), "连接异常", "检查 Emby 地址、网络连通性和 API Key。"),
        ("permission", ("401", "403", "unauthorized", "forbidden", "权限"), "权限异常", "检查 Emby API Key 是否有效并具有媒体库访问权限。"),
        ("image", ("image", "poster", "backdrop", "封面", "海报", "背景"), "图片处理异常", "检查素材地址是否可访问，以及图片格式和尺寸是否有效。"),
        ("webhook", ("webhook", "payload"), "Webhook 异常", "检查 Emby Webhook 地址、事件类型和请求内容。"),
    )
    explanations = []
    for key, tokens, title, detail in rules:
        matched = sum(1 for message in issues if any(token in message for token in tokens))
        if matched:
            explanations.append({"key": key, "title": title, "detail": detail, "matched": matched})
    return explanations


def summarize_log_file(path, limit=250, category="all", level="all", hours=0, now=None):
    limit = max(1, min(int(limit or 250), 2000))
    hours = max(0, min(int(hours or 0), 24 * 30))
    category = category if category in {"all", "system", "cover", "webhook", "notify", "emby"} else "all"
    level = str(level or "all").upper()
    if level not in {"ALL", *DISPLAY_LEVELS}:
        level = "ALL"

    file_info = {
        "path": "config/app.log",
        "size": 0,
        "modified": None,
    }
    if not os.path.isfile(path):
        return {
            "scoped_total": 0,
            "shown": 0,
            "categories": {name: 0 for name in ("system", "cover", "webhook", "notify", "emby")},
            "levels": {name: 0 for name in DISPLAY_LEVELS},
            "entries": [],
            "hotspots": [],
            "explanations": [],
            "last_issue": None,
            "file": file_info,
        }

    stat = os.stat(path)
    file_info.update({
        "size": stat.st_size,
        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(timespec="seconds"),
    })
    with open(path, "r", encoding="utf-8", errors="replace") as log_file:
        all_lines = log_file.readlines()

    start_index = max(0, len(all_lines) - limit)
    entries = [
        _parse_log_line(raw, f"log-{start_index + offset}")
        for offset, raw in enumerate(all_lines[start_index:])
        if raw.strip()
    ]

    if hours:
        cutoff = (now or datetime.now()) - timedelta(hours=hours)
        entries = [entry for entry in entries if entry["_datetime"] is None or entry["_datetime"] >= cutoff]

    scoped_entries = entries
    category_counts = Counter(entry["category"] for entry in scoped_entries)
    level_counts = Counter(entry["level"] for entry in scoped_entries)

    filtered_entries = [
        entry for entry in scoped_entries
        if (category == "all" or entry["category"] == category)
        and (level == "ALL" or entry["level"] == level)
    ]
    issue_entries = [entry for entry in filtered_entries if entry["level"] in ("WARNING", "ERROR")]
    last_issue = None
    if issue_entries:
        latest = issue_entries[-1]
        last_issue = {
            "time": latest["time"],
            "level": latest["level"],
            "category": latest["category"],
            "message": latest["message"],
        }

    public_entries = []
    for entry in filtered_entries:
        public_entries.append({key: value for key, value in entry.items() if key != "_datetime"})

    return {
        "scoped_total": len(scoped_entries),
        "shown": len(public_entries),
        "categories": {name: category_counts.get(name, 0) for name in ("system", "cover", "webhook", "notify", "emby")},
        "levels": {name: level_counts.get(name, 0) for name in DISPLAY_LEVELS},
        "entries": public_entries,
        "hotspots": _build_hotspots(filtered_entries),
        "explanations": _build_explanations(filtered_entries),
        "last_issue": last_issue,
        "file": file_info,
    }
