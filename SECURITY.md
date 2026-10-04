# Security & Compliance Policy

This document describes the threat model, defensive controls, and compliance procedures for the WhatsApp AI Agent.

---

## 1. Threat Model & Mitigations

| Threat | Risk | Defensive Control |
|---|---|---|
| **Webhook Spoofing** | High | `X-Hub-Signature-256` header validated via HMAC-SHA256 with `WHATSAPP_APP_SECRET`. Unsigned/invalid payloads receive immediate 403 Forbidden. |
| **Replay & Duplicate Attacks** | High | Idempotent deduplication in Redis (`SET wa:msg:<id> 1 NX EX 86400`). Duplicate payloads ACK with 200 but drop processing. |
| **Prompt Injection** | High | Server-side authorization locks tools to server-verified `wa_id`. Claude is instructed in the system prompt to treat user text strictly as untrusted input. |
| **PII & Data Leakage** | Medium | Phone numbers are masked in all application logs (`+15 ••••• 4567`). API tokens and authorization headers are never logged. |
| **Rate Limit & Denial of Service** | Medium | Per-`wa_id` Redis sliding-window rate limiter throttles traffic exceeding 10 messages/min. |
| **Unauthorized Staff Access** | High | Admin API uses Argon2 password hashing and httpOnly JWT session cookies with `SameSite=Lax`. |
| **Unauthorized Side Effects** | High | Critical business actions (`cancel_order`, `initiate_refund`) enforce a strict 2-step confirmation requirement. |

---

## 2. Meta Cloud API Compliance Checklist

- [x] **Webhook Signature**: HMAC-SHA256 verified on all inbound requests.
- [x] **Fast Acknowledgement**: Webhook responds HTTP 200 within 200ms; workload deferred to async workers.
- [x] **Opt-Out Handling**: Immediate compliance with `STOP`, `UNSUBSCRIBE`, `CANCEL`.
- [x] **24-Hour Customer Window**: Free-form text blocked when `now - last_user_msg_at > 24h`; templates enforced.
- [x] **Permanent Tokens**: System User tokens utilized in production rather than 24-hour developer tokens.
- [x] **PII Protection**: User data protected according to GDPR/CCPA standards.
