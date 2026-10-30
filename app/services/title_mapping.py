def normalize_title_mapping(raw_mapping):
    """Normalize legacy subtitle-only mappings and new title/subtitle mappings."""
    normalized = {}
    if not isinstance(raw_mapping, dict):
        return normalized

    for key, value in raw_mapping.items():
        library_name = str(key).strip()
        if not library_name:
            continue

        if isinstance(value, dict):
            normalized[library_name] = {
                "title": str(value.get("title") or "").strip(),
                "subtitle": str(value.get("subtitle") or value.get("val") or "").strip(),
            }
        else:
            normalized[library_name] = {
                "title": "",
                "subtitle": str(value or "").strip(),
            }
    return normalized


def apply_title_mapping(config, library_name, raw_mapping):
    """Apply configured cover title/subtitle text for a library name."""
    mapped = normalize_title_mapping(raw_mapping).get(library_name, {})
    title = mapped.get("title") or library_name
    subtitle = mapped.get("subtitle")

    next_config = dict(config or {})
    next_config["title"] = title
    # A subtitle is optional. Never synthesize one from the library or title
    # when the user has not configured a translation.
    next_config["subtitle"] = subtitle or ""
    return next_config
