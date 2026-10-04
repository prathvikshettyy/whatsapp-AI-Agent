"""Webhook endpoint tests."""

import hashlib
import hmac
import json
from unittest.mock import AsyncMock
import pytest

from backend.app.config import settings


def compute_sig(secret: str, body: bytes) -> str:
    digest = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_webhook_get_verification_success(async_client):
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": settings.WHATSAPP_VERIFY_TOKEN,
        "hub.challenge": "test_challenge_12345",
    }
    resp = await async_client.get("/webhook", params=params)
    assert resp.status_code == 200
    assert resp.text == "test_challenge_12345"


@pytest.mark.asyncio
async def test_webhook_get_verification_invalid_token(async_client):
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong_token",
        "hub.challenge": "test_challenge_12345",
    }
    resp = await async_client.get("/webhook", params=params)
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_webhook_post_signature_and_dedupe(async_client, monkeypatch):
    mock_task = AsyncMock()
    monkeypatch.setattr("backend.app.api.webhook.process_inbound", mock_task)

    payload = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "messages": [
                                {
                                    "from": "15550001",
                                    "id": "wamid.001",
                                    "type": "text",
                                    "text": {"body": "Hello"},
                                }
                            ]
                        }
                    }
                ]
            }
        ]
    }
    body = json.dumps(payload).encode("utf-8")
    sig = compute_sig(settings.WHATSAPP_APP_SECRET, body)

    # 1. First delivery
    resp1 = await async_client.post("/webhook", content=body, headers={"X-Hub-Signature-256": sig})
    assert resp1.status_code == 200
    assert mock_task.call_count == 1

    # 2. Second duplicate delivery (Meta retry) -> fast ACK 200 but deduplicated
    resp2 = await async_client.post("/webhook", content=body, headers={"X-Hub-Signature-256": sig})
    assert resp2.status_code == 200
    assert mock_task.call_count == 1


@pytest.mark.asyncio
async def test_webhook_post_invalid_signature(async_client):
    body = json.dumps({"entry": []}).encode("utf-8")
    resp = await async_client.post("/webhook", content=body, headers={"X-Hub-Signature-256": "sha256=invalid"})
    assert resp.status_code == 403
