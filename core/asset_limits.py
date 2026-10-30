NINE_GRID_ENGINES = {"旋转堆叠", "经典九宫格", "经典九宫格(动态)"}


def resolve_asset_limits(config):
    config = config or {}
    engine = str(config.get("engine") or "")
    default_posters = 9 if engine in NINE_GRID_ENGINES else 6
    poster_limit = max(0, int(config.get("poster_count", default_posters)))
    is_dynamic = bool(config.get("enable_animation")) or engine.endswith("(动态)")
    backdrop_limit = poster_limit if is_dynamic else max(0, int(config.get("backdrop_count", 1)))
    return poster_limit, backdrop_limit
