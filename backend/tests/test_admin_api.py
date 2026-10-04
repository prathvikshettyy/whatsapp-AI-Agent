"""Admin API endpoints and 24h window tests."""

from datetime import datetime, timedelta, timezone
import pytest

from backend.app.models.contact import Contact
from backend.app.models.conversation import Conversation
from backend.app.models.message import Message


@pytest.mark.asyncio
async def test_auth_login_and_me(async_client):
    login_resp = await async_client.post(
        "/auth/login",
        json={"email": "admin@company.com", "password": "securepassword123"},
    )
    assert login_resp.status_code == 200
    assert "staff_token" in login_resp.cookies

    me_resp = await async_client.get("/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "admin@company.com"


@pytest.mark.asyncio
async def test_takeover_and_release(async_client, db_session):
    contact = Contact(wa_id="15550002", name="Alice")
    db_session.add(contact)
    await db_session.flush()

    conv = Conversation(contact_id=contact.id, status="bot")
    db_session.add(conv)
    await db_session.commit()
    await db_session.refresh(conv)

    # Takeover
    t_resp = await async_client.post(f"/conversations/{conv.id}/takeover")
    assert t_resp.status_code == 200
    assert t_resp.json()["status"] == "human"

    # Release
    r_resp = await async_client.post(f"/conversations/{conv.id}/release")
    assert r_resp.status_code == 200
    assert r_resp.json()["status"] == "bot"


@pytest.mark.asyncio
async def test_24h_window_send_enforcement(async_client, db_session):
    contact = Contact(wa_id="15550003", name="Bob")
    db_session.add(contact)
    await db_session.flush()

    # Conversation outside 24h window (30 hours ago)
    thirty_hours_ago = datetime.now(timezone.utc) - timedelta(hours=30)
    expired_conv = Conversation(
        contact_id=contact.id,
        status="human",
        last_user_msg_at=thirty_hours_ago,
    )
    db_session.add(expired_conv)
    await db_session.commit()
    await db_session.refresh(expired_conv)

    # Attempting to send free-text message outside 24h window must be rejected
    resp_expired = await async_client.post(
        f"/conversations/{expired_conv.id}/send",
        json={"content": "Hello customer, here is an update"},
    )
    assert resp_expired.status_code == 400
    assert "24-hour" in resp_expired.json()["detail"]

    # Conversation within 24h window (1 hour ago)
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    active_conv = Conversation(
        contact_id=contact.id,
        status="human",
        last_user_msg_at=one_hour_ago,
    )
    db_session.add(active_conv)
    await db_session.commit()
    await db_session.refresh(active_conv)

    resp_active = await async_client.post(
        f"/conversations/{active_conv.id}/send",
        json={"content": "Hello customer, we are working on it"},
    )
    assert resp_active.status_code == 200
    assert resp_active.json()["content"] == "Hello customer, we are working on it"


@pytest.mark.asyncio
async def test_settings_and_prompt_history(async_client):
    # Initial get
    get_resp = await async_client.get("/settings")
    assert get_resp.status_code == 200
    initial_ver = get_resp.json()["version"]

    # Update prompt
    put_resp = await async_client.put(
        "/settings",
        json={
            "system_prompt": "Updated custom Claude prompt for testing.",
            "version_summary": "Test update prompt",
        },
    )
    assert put_resp.status_code == 200
    assert put_resp.json()["version"] == initial_ver + 1

    # Verify history
    hist_resp = await async_client.get("/settings/prompt-history")
    assert hist_resp.status_code == 200
    assert len(hist_resp.json()) >= 1


@pytest.mark.asyncio
async def test_kb_crud(async_client):
    # Create
    create_resp = await async_client.post(
        "/kb",
        json={"title": "Test Shipping", "body": "Standard shipping takes 3-5 days."},
    )
    assert create_resp.status_code == 200
    doc_id = create_resp.json()["id"]

    # List
    list_resp = await async_client.get("/kb")
    assert list_resp.status_code == 200
    assert any(d["id"] == doc_id for d in list_resp.json())

    # Update
    up_resp = await async_client.put(
        f"/kb/{doc_id}",
        json={"title": "Updated Shipping", "body": "Takes 2 days."},
    )
    assert up_resp.status_code == 200
    assert up_resp.json()["title"] == "Updated Shipping"

    # Delete
    del_resp = await async_client.delete(f"/kb/{doc_id}")
    assert del_resp.status_code == 200
