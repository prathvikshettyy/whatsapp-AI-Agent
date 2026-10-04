# System Architecture

Enterprise architectural blueprint for the WhatsApp AI Agent and Staff Management Dashboard.

---

## 1. High-Level System Architecture

```
                                  +------------------------------------+
                                  |         WhatsApp Network           |
                                  |  (End-user on iOS / Android / Web) |
                                  +-----------------+------------------+
                                                    |
                                          HTTPS (Cloud API)
                                                    v
                                  +------------------------------------+
                                  |     Meta Graph API (Cloud API)     |
                                  +-----------------+------------------+
                                                    |
                                       POST /webhook (HMAC-SHA256)
                                                    v
+----------------------------------------------------------------------------------------+
|                                    Backend Cluster                                     |
|                                                                                        |
|  +------------------------+          +-------------------+          +---------------+  |
|  |     FastAPI Ingest     | -------> |    Redis (Cache,  | <------- |  arq Worker   |  |
|  | (Webhook, Auth, Admin) |          | Dedupe, Pub/Sub)  |          | (Claude Loop) |  |
|  +------------------------+          +-------------------+          +---------------+  |
|              |                                                              |          |
|              v                                                              v          |
|  +----------------------------------------------------------------------------------+  |
|  |                     PostgreSQL Database (Source of Truth)                        |  |
|  |  (contacts, conversations, messages, tool_calls, kb_docs, settings, staff_users) |  |
|  +----------------------------------------------------------------------------------+  |
|                                                                                        |
+----------------------------------------------------------------------------------------+
              ^                                                              |
              | SSE /stream & REST API                         Claude API & Tools
              |                                                              v
+-----------------------------+                               +--------------------------+
|   React Admin Dashboard     |                               |   Anthropic Claude API   |
|   (Vite, Tailwind, TanStack)|                               | (Prompt Caching & Tools) |
+-----------------------------+                               +--------------------------+
```

---

## 2. Component Responsibilities

1. **FastAPI Webhook Handler**:
   - Immediate verification of Meta HMAC-SHA256 signature (`X-Hub-Signature-256`).
   - Idempotency check with Redis `SET wa:msg:<id> 1 NX EX 86400`.
   - Schedules background task and returns HTTP 200 within <200ms.
2. **arq Asynchronous Worker**:
   - Handles message processing serially per `wa_id` to prevent message interleaving.
   - Loads conversation history from PostgreSQL while preserving tool call pairs.
   - Enforces rate limiting, opt-out compliance, and human handoff routing.
   - Orchestrates Claude agent reasoning loop (max 8 iterations).
   - Sends replies via WhatsApp Cloud API with auto-chunking (>4096 chars).
   - Dispatches live events to Redis pub/sub channel for connected admin dashboards.
3. **PostgreSQL Database**:
   - Canonical source of truth for all contacts, messages, tool audits, and settings.
4. **Redis Service**:
   - Ephemeral cache for deduplication, sliding-window rate limiting, and pub/sub for SSE.
5. **Staff Admin Dashboard (React)**:
   - Real-time conversation monitoring, 24-hour service window badge countdown, one-click takeover/release, and prompt configuration with rollback.
