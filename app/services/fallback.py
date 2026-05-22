from __future__ import annotations

import logging
from abc import ABC, abstractmethod

logger = logging.getLogger("search.fallback")


class SearchFallbackProvider(ABC):
    """Abstract base for commercial search fallback providers.

    Implementations should handle their own error recovery.
    Phase 1: interface only, no concrete providers wired.
    Phase 2+: Tavily, Exa, SerpAPI, Brave Search, Google Programmable Search.
    """

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[dict]:
        """Return a list of result dicts with at least: url, title, snippet."""
        ...

    @abstractmethod
    def name(self) -> str:
        """Provider identifier for metrics/logging."""
        ...


class FallbackOrchestrator:
    """Coordinates fallback provider calls when free engines fail."""

    def __init__(self, providers: list[SearchFallbackProvider] | None = None) -> None:
        self._providers = providers or []

    def register(self, provider: SearchFallbackProvider) -> None:
        self._providers.append(provider)

    async def search(self, query: str, limit: int) -> tuple[list[dict], str | None]:
        """Try providers in order. Returns (results, provider_name) or ([], None)."""
        for provider in self._providers:
            try:
                results = await provider.search(query, limit)
                if results:
                    logger.info("Fallback %s returned %d results", provider.name(), len(results))
                    return results, provider.name()
            except Exception as e:
                logger.warning("Fallback %s failed: %s", provider.name(), e)
                continue
        return [], None


# Module-level singleton (no providers registered in Phase 1)
fallback_orchestrator = FallbackOrchestrator()
