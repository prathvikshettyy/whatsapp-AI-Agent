"""Tests for WhatsApp Cloud API client, message splitting, and phone masking."""

import pytest
import httpx
from app.whatsapp import WhatsAppClient, mask_phone_number, split_message


def test_mask_phone_number():
    assert mask_phone_number("15551234567") == "155****4567"
    assert mask_phone_number("+12345678901") == "+12****8901"
    assert mask_phone_number("123") == "****"
    assert mask_phone_number("") == "unknown"


def test_split_message_short():
    short_text = "Hello, this is a normal message."
    chunks = split_message(short_text, max_length=100)
    assert len(chunks) == 1
    assert chunks[0] == short_text


def test_split_message_long():
    para1 = "Paragraph 1: " + ("A" * 80)
    para2 = "Paragraph 2: " + ("B" * 80)
    full_text = f"{para1}\n\n{para2}"

    chunks = split_message(full_text, max_length=100)
    assert len(chunks) == 2
    assert "Paragraph 1" in chunks[0]
    assert "Paragraph 2" in chunks[1]
    for chunk in chunks:
        assert len(chunk) <= 100


@pytest.mark.asyncio
async def test_send_text_message():
    def custom_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test_token"
        assert request.url.path.endswith("/messages")
        return httpx.Response(200, json={"messages": [{"id": "wamid.123"}]})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(custom_handler))
    wa = WhatsAppClient(
        token="test_token",
        phone_number_id="10099",
        http_client=mock_client,
    )

    responses = await wa.send_text_message(
        to="15551234567",
        text="Hello WhatsApp!",
        reply_to_message_id="msg_orig",
    )
    assert len(responses) == 1
    assert responses[0]["messages"][0]["id"] == "wamid.123"


@pytest.mark.asyncio
async def test_mark_as_read():
    def custom_handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test_token"
        return httpx.Response(200, json={"success": True})

    mock_client = httpx.AsyncClient(transport=httpx.MockTransport(custom_handler))
    wa = WhatsAppClient(token="test_token", phone_number_id="10099", http_client=mock_client)
    res = await wa.mark_as_read("wamid.998877")
    assert res.get("success") is True
