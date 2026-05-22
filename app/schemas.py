from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class QueryProfile(str, Enum):
    GENERAL_CN = "general_cn"
    TECH = "tech"
    WECHAT = "wechat"
    RESEARCH = "research"
    FRESH_CN = "fresh_cn"
    AUTO = "auto"


class Freshness(str, Enum):
    AUTO = "auto"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    YEAR = "year"


class Language(str, Enum):
    AUTO = "auto"
    ZH_CN = "zh-CN"
    EN = "en"
    ALL = "all"


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    profile: str = Field(default="auto")
    limit: int = Field(default=10, ge=1, le=20)
    freshness: str = Field(default="auto")
    language: str = Field(default="auto")
    use_cache: bool = Field(default=True)


class ConfidenceBreakdown(BaseModel):
    searxng_score: float = 0.0
    domain_authority: float = 0.0
    keyword_match: float = 0.0
    engine_consensus: float = 0.0
    freshness: float = 0.0
    source_type: float = 0.0
    penalty: float = 0.0


class SearchResultItem(BaseModel):
    rank: int
    title: str
    url: str
    snippet: str
    domain: str
    source_type: str
    confidence: float
    confidence_breakdown: ConfidenceBreakdown
    engines: list[str]
    why_selected: str | None = None


class EngineSkipReason(BaseModel):
    engine: str
    reason: str


class EngineFailReason(BaseModel):
    engine: str
    reason: str


class SearchMeta(BaseModel):
    total_results: int
    latency_ms: int
    cache_hit: bool
    partial: bool
    engines_used: list[str]
    engines_skipped: list[EngineSkipReason]
    engines_failed: list[EngineFailReason]


class SearchResponse(BaseModel):
    query: str
    profile: str
    query_variants: list[str]
    results: list[SearchResultItem]
    meta: SearchMeta
    warnings: list[str]


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str


class ReadyDependency(BaseModel):
    redis: str
    searxng: str


class ReadyResponse(BaseModel):
    status: str
    dependencies: ReadyDependency


class EngineStatus(BaseModel):
    name: str
    status: str
    cooldown_until: str | None = None
    success_rate_15m: float | None = None
    avg_latency_ms_15m: float | None = None
    last_error: str | None = None


class EnginesStatusResponse(BaseModel):
    engines: list[EngineStatus]
    metrics: dict | None = None


class SearchMetrics(BaseModel):
    timestamp: str
    query: str
    profile: str
    query_hash: str
    latency_ms: int
    cache_hit: bool
    partial: bool
    engines_used: list[str]
    engines_failed: list[str]
    result_count: int
    top_domains: list[str]
    fallback_used: bool
