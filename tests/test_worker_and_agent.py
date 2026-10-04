"""Tests for worker logic, human handoff, opt-out compliance, and agent tool execution."""

from unittest.mock import AsyncMock, MagicMock
import pytest
import httpx

from app.agent import WhatsAppAgent
from app.store import RedisStore
from app.tools import execute_tool
from app.whatsapp import WhatsAppClient
from app.worker import process_message


@pytest.mark.asyncio
async def test_tool_sensitive_confirmation_check():
    # Calling cancel_order without confirmation should return requires_user_confirmation
    res = await execute_tool("cancel_order", {"order_id": "ORD-1029"}, "15551111", confirmed=False)
    assert res["status"] == "requires_user_confirmation"

    # Calling cancel_order WITH confirmation executes cancellation
    res_confirmed = await execute_tool("cancel_order", {"order_id": "ORD-1029"}, "15551111", confirmed=True)
    assert res_confirmed["status"] == "cancelled"


@pytest.mark.asyncio
async def test_tool_check_order_status():
    res = await execute_tool("check_order_status", {"order_id": "ORD-1029"}, "15551111")
    assert "order" in res
    assert res["order"]["status"] == "In Transit" or "Cancelled" in res["order"]["status"]


@pytest.mark.asyncio
async def test_worker_opt_out_stop(fake_store):
    sent_messages = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        body = json.loads(request.content.decode("utf-8"))
        sent_messages.append(body)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    wa_client = WhatsAppClient(token="t", phone_number_id="p", http_client=mock_client)

    msg = {
        "from": "15550009",
        "id": "wamid.msg1",
        "type": "text",
        "text": {"body": "STOP"},
    }

    await process_message(msg, store=fake_store, whatsapp=wa_client)

    # Must be marked opted out in store
    assert await fake_store.is_opted_out("15550009") is True

    # Must send unsubscribe confirmation text
    assert len(sent_messages) >= 1
    assert "unsubscribed" in sent_messages[-1]["text"]["body"].lower()


@pytest.mark.asyncio
async def test_worker_human_handoff(fake_store):
    sent_messages = []

    def mock_handler(request: httpx.Request) -> httpx.Response:
        import json
        body = json.loads(request.content.decode("utf-8"))
        sent_messages.append(body)
        return httpx.Response(200, json={"messages": [{"id": "wamid.out"}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(mock_handler))
    wa_client = WhatsAppClient(token="t", phone_number_id="p", http_client=mock_client)

    msg = {
        "from": "15550010",
        "id": "wamid.msg2",
        "type": "text",
        "text": {"body": "agent"},
    }

    await process_message(msg, store=fake_store, whatsapp=wa_client)

    # Conversation should be flagged for human handoff
    assert await fake_store.is_handed_off("15550010") is True

    # Must notify user about human handoff
    assert len(sent_messages) >= 1
    assert "human support agent" in sent_messages[-1]["text"]["body"]


@pytest.mark.asyncio
async def test_agent_tool_loop_mock(fake_store):
    # Mock Anthropic Messages client
    mock_anthropic = MagicMock()
    mock_messages = AsyncMock()

    # Step 1: Claude decides to call check_order_status
    tool_use_block = MagicMock()
    tool_use_block.type = "tool_use"
    tool_use_block.name = "check_order_status"
    tool_use_block.input = {"order_id": "ORD-2045"}
    tool_use_block.id = "tool_call_1"

    step1_response = MagicMock()
    step1_response.stop_reason = "tool_use"
    step1_response.content = [tool_use_block]

    # Step 2: Claude answers with final formatted text
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = "Your order *ORD-2045* is currently *Processing*."

    step2_response = MagicMock()
    step2_response.stop_reason = "end_turn"
    step2_response.content = [text_block]

    mock_messages.create.side_effect = [step1_response, step2_response]
    mock_anthropic.messages = mock_messages

    agent = WhatsAppAgent(anthropic_client=mock_anthropic, store=fake_store)
    result = await agent.process_user_turn(
        wa_id="15550020",
        user_text="What is the status of my order ORD-2045?",
    )

    assert "ORD-2045" in result
    assert "Processing" in result
    # History should have been recorded
    history = await fake_store.get_history("15550020")
    assert len(history) == 2
    assert history[0]["content"] == "What is the status of my order ORD-2045?"
    assert "ORD-2045" in history[1]["content"]
