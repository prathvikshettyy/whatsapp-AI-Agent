"""Tests for RedisStore operations: dedupe, rate-limit, history, opt-out, handoff."""

import pytest


@pytest.mark.asyncio
async def test_deduplication(fake_store):
    msg_id = "msg_abc123"
    # First check should be True (new message)
    is_new = await fake_store.check_and_set_dedupe(msg_id, ttl=60)
    assert is_new is True

    # Immediate second check must be False (duplicate)
    is_duplicate = await fake_store.check_and_set_dedupe(msg_id, ttl=60)
    assert is_duplicate is False


@pytest.mark.asyncio
async def test_rate_limiting(fake_store):
    user_id = "15550001"
    limit = 3
    window = 60

    # First 3 should pass
    for _ in range(limit):
        assert await fake_store.check_rate_limit(user_id, limit=limit, window=window) is True

    # 4th should exceed limit
    assert await fake_store.check_rate_limit(user_id, limit=limit, window=window) is False


@pytest.mark.asyncio
async def test_chat_history(fake_store):
    user_id = "15550002"

    await fake_store.add_turn(user_id, "user", "What are your hours?")
    await fake_store.add_turn(user_id, "assistant", "We are open 9am to 6pm.")

    history = await fake_store.get_history(user_id, max_turns=10)
    assert len(history) == 2
    assert history[0]["role"] == "user"
    assert history[0]["content"] == "What are your hours?"
    assert history[1]["role"] == "assistant"
    assert "9am" in history[1]["content"]

    await fake_store.clear_history(user_id)
    history_after_clear = await fake_store.get_history(user_id)
    assert len(history_after_clear) == 0


@pytest.mark.asyncio
async def test_opt_out_and_opt_in(fake_store):
    user_id = "15550003"
    assert await fake_store.is_opted_out(user_id) is False

    await fake_store.set_opt_out(user_id, True)
    assert await fake_store.is_opted_out(user_id) is True

    await fake_store.set_opt_out(user_id, False)
    assert await fake_store.is_opted_out(user_id) is False


@pytest.mark.asyncio
async def test_human_handoff(fake_store):
    user_id = "15550004"
    assert await fake_store.is_handed_off(user_id) is False

    await fake_store.set_handoff(user_id, True)
    assert await fake_store.is_handed_off(user_id) is True

    await fake_store.set_handoff(user_id, False)
    assert await fake_store.is_handed_off(user_id) is False


@pytest.mark.asyncio
async def test_pending_confirmation(fake_store):
    user_id = "15550005"
    assert await fake_store.get_pending_action(user_id) is None

    action = {"tool": "cancel_order", "order_id": "ORD-1029"}
    await fake_store.set_pending_action(user_id, action)

    retrieved = await fake_store.get_pending_action(user_id)
    assert retrieved == action

    await fake_store.clear_pending_action(user_id)
    assert await fake_store.get_pending_action(user_id) is None
