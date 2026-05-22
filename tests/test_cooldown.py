import pytest

from app.services.cooldown import CooldownManager


@pytest.mark.asyncio
async def test_cooldown_trigger_and_check(mock_cooldown_manager):
    await mock_cooldown_manager.trigger_cooldown("baidu", "HTTP_429", 10)
    assert await mock_cooldown_manager.is_cooling_down("baidu") is True
    assert await mock_cooldown_manager.is_cooling_down("bing") is False


@pytest.mark.asyncio
async def test_cooldown_handle_error_403(mock_cooldown_manager):
    await mock_cooldown_manager.handle_error("baidu", 403, None)
    assert await mock_cooldown_manager.is_cooling_down("baidu") is True


@pytest.mark.asyncio
async def test_cooldown_handle_error_429(mock_cooldown_manager):
    await mock_cooldown_manager.handle_error("baidu", 429, None)
    assert await mock_cooldown_manager.is_cooling_down("baidu") is True


@pytest.mark.asyncio
async def test_cooldown_timeout_count(mock_cooldown_manager):
    for _ in range(4):
        await mock_cooldown_manager.record_timeout("sogou")
    assert await mock_cooldown_manager.is_cooling_down("sogou") is False
    await mock_cooldown_manager.record_timeout("sogou")
    assert await mock_cooldown_manager.is_cooling_down("sogou") is True


@pytest.mark.asyncio
async def test_cooldown_captcha(mock_cooldown_manager):
    await mock_cooldown_manager.handle_error("baidu", 200, "Please complete the captcha verification")
    assert await mock_cooldown_manager.is_cooling_down("baidu") is True


@pytest.mark.asyncio
async def test_cooldown_connection_fail(mock_cooldown_manager):
    await mock_cooldown_manager.handle_error("sogou", None, None)
    assert await mock_cooldown_manager.is_cooling_down("sogou") is True


@pytest.mark.asyncio
async def test_cooldown_list_all(mock_cooldown_manager):
    await mock_cooldown_manager.trigger_cooldown("baidu", "HTTP_429", 60)
    await mock_cooldown_manager.trigger_cooldown("sogou", "HTTP_403", 60)
    result = await mock_cooldown_manager.list_all()
    engines = [r["engine"] for r in result]
    assert "baidu" in engines
    assert "sogou" in engines


@pytest.mark.asyncio
async def test_cooldown_reset_timeout_count(mock_cooldown_manager):
    for _ in range(3):
        await mock_cooldown_manager.record_timeout("bing")
    await mock_cooldown_manager.reset_timeout_count("bing")
    # After reset, 4 more timeouts should NOT trigger cooldown (counter restarted)
    for _ in range(4):
        await mock_cooldown_manager.record_timeout("bing")
    assert await mock_cooldown_manager.is_cooling_down("bing") is False
    # 5th should trigger
    await mock_cooldown_manager.record_timeout("bing")
    assert await mock_cooldown_manager.is_cooling_down("bing") is True
