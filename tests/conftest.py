from __future__ import annotations

import pytest
import fakeredis.aioredis


@pytest.fixture
def fake_redis():
    """Provide a fake Redis instance for testing."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def mock_cooldown_manager(fake_redis, monkeypatch):
    """Provide a CooldownManager with a fake Redis backend."""
    from app.services.cooldown import CooldownManager

    mgr = CooldownManager()
    monkeypatch.setattr(mgr, "_client", fake_redis)
    return mgr
