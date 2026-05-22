from __future__ import annotations

from app.config import gateway_config
from app.schemas import QueryProfile


def get_engines(profile: QueryProfile | str) -> list[str]:
    profile_str = profile.value if isinstance(profile, QueryProfile) else profile
    cfg = gateway_config.profiles.get(profile_str)
    if cfg:
        return list(cfg.engines)
    return list(gateway_config.profiles["general_cn"].engines)


def get_profile_timeout(profile: QueryProfile | str) -> float:
    profile_str = profile.value if isinstance(profile, QueryProfile) else profile
    cfg = gateway_config.profiles.get(profile_str)
    if cfg:
        return cfg.timeout_seconds
    return gateway_config.searxng.default_timeout_seconds


def get_profile_language(profile: QueryProfile | str) -> str:
    profile_str = profile.value if isinstance(profile, QueryProfile) else profile
    cfg = gateway_config.profiles.get(profile_str)
    if cfg:
        return cfg.language
    return "all"


def get_profile_time_range(profile: QueryProfile | str) -> str | None:
    profile_str = profile.value if isinstance(profile, QueryProfile) else profile
    cfg = gateway_config.profiles.get(profile_str)
    if cfg:
        return cfg.time_range
    return None
