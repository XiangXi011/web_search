import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ServerConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8011


class SearXNGConfig(BaseModel):
    base_url: str = "http://searxng:8080"
    search_path: str = "/search"
    default_timeout_seconds: float = 3.5
    global_deadline_seconds: float = 4.0


class RedisConfig(BaseModel):
    url: str = "redis://redis:6379/0"
    cache_ttl_seconds: int = 3600
    cooldown_prefix: str = "engine_cooldown:"
    cache_prefix: str = "search_cache:"


class SearchConfig(BaseModel):
    default_limit: int = 10
    max_limit: int = 20
    enable_partial_results: bool = True
    min_results_before_fallback: int = 3
    enable_commercial_fallback: bool = False


class CooldownConfig(BaseModel):
    http_403_seconds: int = 900
    http_429_seconds: int = 900
    captcha_seconds: int = 1800
    timeout_fail_threshold: int = 5
    timeout_cooldown_seconds: int = 300
    connection_fail_seconds: int = 180


class ProfileConfig(BaseModel):
    engines: list[str]
    language: str = "all"
    time_range: str | None = None
    timeout_seconds: float = 3.5


class ScoringWeights(BaseModel):
    searxng_score: float = 0.25
    domain_authority: float = 0.25
    keyword_match: float = 0.20
    source_type: float = 0.15
    engine_consensus: float = 0.10
    freshness: float = 0.05


class ScoringConfig(BaseModel):
    weights: ScoringWeights = Field(default_factory=ScoringWeights)
    source_type_scores: dict[str, float] = Field(default_factory=dict)


class DedupConfig(BaseModel):
    default_max_per_domain: int = 2
    domain_limits: dict[str, int] = Field(default_factory=dict)
    title_similarity_threshold: float = 0.92
    snippet_similarity_threshold: float = 0.9


class GatewayConfig(BaseModel):
    server: ServerConfig = Field(default_factory=ServerConfig)
    searxng: SearXNGConfig = Field(default_factory=SearXNGConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    cooldown: CooldownConfig = Field(default_factory=CooldownConfig)
    profiles: dict[str, ProfileConfig] = Field(default_factory=dict)
    scoring: ScoringConfig = Field(default_factory=ScoringConfig)
    dedup: DedupConfig = Field(default_factory=DedupConfig)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    config_path: str = Field(default="config.yml", alias="CONFIG_PATH")
    version: str = "0.1.0"


def _merge_dicts(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result


def load_config(config_path: str | None = None) -> GatewayConfig:
    path = Path(config_path or os.getenv("CONFIG_PATH", "config.yml"))
    if not path.exists():
        return GatewayConfig()

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return GatewayConfig.model_validate(raw)


# Global singleton; initialized in lifespan
settings = Settings()
gateway_config = load_config(settings.config_path)
