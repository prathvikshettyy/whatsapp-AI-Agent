"""Service layer tests: whatsapp client, rate limiting, and tool gating."""

from unittest.mock import AsyncMock, MagicMock
import pytest

from backend.app.services.agent import AgentService
from backend.app.services.ratelimit import check_rate_limit
from backend.app.services.tools.registry import run_tool
from backend.app.services.whatsapp import mask_phone_number, split_message


def test_phone_masking():
    assert mask_phone_number("+15551234567") == "+15 ••••• 4567"
    assert mask_phone_number("123") == "****"
    assert mask_phone_number("") == "unknown"


def test_split_long_message():
    text = "Line 1\n\n" + ("A" * 100) + "\n\n" + ("B" * 100)
    chunks = split_message(text, max_length=120)
    assert len(chunks) >= 2
    for c in chunks:
        assert len(c) <= 120


@pytest.mark.asyncio
async def test_sliding_window_rate_limiting(fake_redis):
    wa_id = "15559999"
    limit = 3

    for _ in range(limit):
        assert await check_rate_limit(wa_id, limit=limit, window=60) is True

    # 4th message exceeds limit
    assert await check_rate_limit(wa_id, limit=limit, window=60) is False


@pytest.mark.asyncio
async def test_sensitive_tool_gating():
    # Calling without confirmation returns requires_user_confirmation
    unconfirmed = await run_tool("cancel_order", {"order_id": "ORD-1029"}, "15559999", confirmed=False)
    assert unconfirmed["status"] == "requires_user_confirmation"

    # Calling with confirmation proceeds to cancel
    confirmed = await run_tool("cancel_order", {"order_id": "ORD-1029"}, "15559999", confirmed=True)
    assert confirmed["status"] == "cancelled"


@pytest.mark.asyncio
async def test_agent_loop_mock():
    mock_client = MagicMock()
    mock_messages = AsyncMock()

    # Step 1: tool use
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.id = "tc_1"
    tool_block.name = "check_order_status"
    tool_block.input = {"order_id": "ORD-1029"}

    step1_resp = MagicMock()
    step1_resp.stop_reason = "tool_use"
    step1_resp.content = [tool_block]
    step1_resp.usage = MagicMock(input_tokens=10, output_tokens=15)

    # Step 2: final reply
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Your order *ORD-1029* is *In Transit* with FedEx."

    step2_resp = MagicMock()
    step2_resp.stop_reason = "end_turn"
    step2_resp.content = [text_block]
    step2_resp.usage = MagicMock(input_tokens=25, output_tokens=30)

    mock_messages.create.side_effect = [step1_resp, step2_resp]
    mock_client.messages = mock_messages

    agent = AgentService(client=mock_client)
    reply, tool_audits, t_in, t_out = await agent.run(
        messages=[{"role": "user", "content": "Where is my order ORD-1029?"}],
        wa_id="15551234",
    )

    assert "ORD-1029" in reply
    assert "In Transit" in reply
    assert len(tool_audits) == 1
    assert tool_audits[0]["name"] == "check_order_status"
    assert t_in == 35
    assert t_out == 45
