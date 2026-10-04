"""Tests for WhatsApp Webhook GET and POST endpoints."""

import hashlib
import hmac
import json
import pytest
from unittest.mock import AsyncMock, patch
from httpx import ASGITransport, AsyncClient

from app.config import settings
from app.main import app
from app.store import store


def compute_signature(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_get_webhook_verification_success():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "1122334455_challenge",
        }
        response = await client.get("/webhook", params=params)
        assert response.status_code == 200
        assert response.text == "1122334455_challenge"


@pytest.mark.asyncio
async def test_get_webhook_verification_invalid_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        params = {
            "hub.mode": "subscribe",
            "hub.verify_token": "wrong_token",
            "hub.challenge": "1122334455_challenge",
        }
        response = await client.get("/webhook", params=params)
        assert response.status_code == 403
        assert "Forbidden" in response.text


@pytest.mark.asyncio
async def test_get_webhook_verification_invalid_mode():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        params = {
            "hub.mode": "publish",
            "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
            "hub.challenge": "1122334455_challenge",
        }
        response = await client.get("/webhook", params=params)
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_post_webhook_valid_signature_and_dedupe(fake_redis, monkeypatch):
    monkeypatch.setattr(store, "_redis", fake_redis)

    mock_process = AsyncMock()
    mock_enqueue = AsyncMock()
    monkeypatch.setattr("app.main.process_message", mock_process)
    monkeypatch.setattr("app.main.enqueue_message", mock_enqueue)

    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {"display_phone_number": "12345", "phone_number_id": "1000999888"},
                            "messages": [
                                {
                                    "from": "15551234567",
                                    "id": "wamid.HBgLMTU1NTEyMzQ1NjcVAgASGBQz",
                                    "timestamp": "1710000000",
                                    "text": {"body": "Hello"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = compute_signature(settings.WHATSAPP_APP_SECRET, raw_body)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First send: should succeed, enqueue tasks, and dedupe key set
        headers = {"X-Hub-Signature-256": sig, "Content-Type": "application/json"}
        resp1 = await client.post("/webhook", content=raw_body, headers=headers)
        assert resp1.status_code == 200
        assert mock_process.call_count == 1
        assert mock_enqueue.call_count == 1

        # Second send of identical message id: should return 200 fast ACK but skip enqueue
        resp2 = await client.post("/webhook", content=raw_body, headers=headers)
        assert resp2.status_code == 200
        assert mock_process.call_count == 1  # Deduplicated, count did not increase!
        assert mock_enqueue.call_count == 1


@pytest.mark.asyncio
async def test_post_webhook_invalid_signature():
    payload = {"entry": []}
    raw_body = json.dumps(payload).encode("utf-8")
    headers = {"X-Hub-Signature-256": "sha256=invalidhexdigest12345", "Content-Type": "application/json"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/webhook", content=raw_body, headers=headers)
        assert resp.status_code == 403
        assert "Invalid signature" in response_text if (response_text := resp.text) else True


@pytest.mark.asyncio
async def test_post_webhook_status_event_ignored(fake_redis, monkeypatch):
    monkeypatch.setattr(store, "_redis", fake_redis)

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "statuses": [
                                {
                                    "id": "wamid.HBgLMTU1",
                                    "status": "delivered",
                                    "timestamp": "1710000005",
                                    "recipient_id": "15551234567",
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    raw_body = json.dumps(payload).encode("utf-8")
    sig = compute_signature(settings.WHATSAPP_APP_SECRET, raw_body)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        headers = {"X-Hub-Signature-256": sig, "Content-Type": "application/json"}
        resp = await client.post("/webhook", content=raw_body, headers=headers)
        assert resp.status_code == 200
