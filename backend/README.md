# WhatsApp AI Agent Backend

Enterprise WhatsApp Business Platform backend with FastAPI, PostgreSQL (SQLAlchemy 2 + Alembic), Redis, arq asynchronous worker, and Anthropic Claude.

---

## Architecture & Data Flow

```
WhatsApp User -> Meta Cloud API -> POST /webhook (FastAPI)
                                         |
                                 verify signature, dedupe (Redis)
                                         |
                                     arq worker
                                         |
             load history (Postgres) -> Claude API + tools -> loop until text
                                         |
             save message & tool audit (Postgres) -> publish SSE (Redis pub/sub)
                                         |
             POST graph.facebook.com/<PHONE_NUMBER_ID>/messages -> User
```

1. **Meta Webhook Router**: Reads raw body, validates `X-Hub-Signature-256` HMAC-SHA256 with `WHATSAPP_APP_SECRET`, dedupes on `message.id` (`SET wa:msg:<id> 1 NX EX 86400`), enqueues `process_inbound` task to arq worker, and immediately returns 200.
2. **Worker Processing**:
   - Upserts `Contact` and `Conversation` in PostgreSQL.
   - Enforces **Rate Limiting** via Redis sliding window.
   - Handles **Opt-Out Compliance** ("STOP") and **Human Handoff** ("AGENT").
   - If conversation status is `human`, stores inbound message and skips Claude.
   - Checks **24-hour service window**; rejects free-text sends outside 24h.
   - Loads chat turns from PostgreSQL while guaranteeing `tool_use`/`tool_result` pairs remain intact.
   - Runs Claude reasoning loop with business tools (capped at 8 steps).
   - Saves message, tool calls, and token metrics to PostgreSQL.
   - Publishes live event over Redis pub/sub channel for real-time dashboard updates.

---

## Directory Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, middleware, lifespan, router registrations, /health
│   ├── config.py            # pydantic-settings environment configuration
│   ├── db.py                # Async engine, sessionmaker, Base model
│   ├── models/              # SQLAlchemy 2 models
│   │   ├── contact.py       # WhatsApp user contact
│   │   ├── conversation.py  # Conversation state (bot, human, closed)
│   │   ├── message.py       # Chat messages, tokens, and media references
│   │   ├── tool_call.py     # Tool execution audit trail
│   │   ├── kb_doc.py        # Knowledge base FAQ documents
│   │   ├── setting.py       # System prompt & version history
│   │   ├── staff_user.py    # Staff authentication & RBAC
│   │   └── audit_log.py     # Staff actions audit trail
│   ├── schemas/             # Pydantic request/response schemas
│   │   ├── auth.py
│   │   ├── conversation.py
│   │   ├── kb.py
│   │   ├── setting.py
│   │   └── analytics.py
│   ├── api/                 # API routers
│   │   ├── webhook.py       # GET/POST /webhook
│   │   ├── auth.py          # /auth/login, /auth/me, /auth/logout
│   │   ├── conversations.py # List, messages, takeover, release, send
│   │   ├── kb.py            # Knowledge base CRUD
│   │   ├── settings.py      # System prompt versioning & rollback
│   │   ├── stream.py        # Server-Sent Events (SSE) with 15s keepalive
│   │   ├── analytics.py     # SQL aggregated metrics
│   │   └── deps.py          # Auth & DB session dependencies
│   ├── services/
│   │   ├── whatsapp.py      # WhatsApp Cloud API client (send, split >4096, mark read)
│   │   ├── agent.py         # Claude tool-calling loop with safety gates
│   │   ├── tools/
│   │   │   └── registry.py  # Tool schemas, dispatch, and sensitive confirmation gate
│   │   ├── history.py       # PostgreSQL history loader preserving tool pairs
│   │   ├── ratelimit.py     # Redis sliding window limiter
│   │   └── events.py        # Redis pub/sub publisher for SSE
│   ├── worker/
│   │   ├── tasks.py         # arq process_inbound worker task
│   │   └── settings.py      # arq WorkerSettings
│   └── security/
│       ├── signature.py     # X-Hub-Signature-256 HMAC verification
│       ├── passwords.py     # Argon2 password hashing
│       └── jwt.py           # JWT token generation & verification
├── alembic/                 # Database migrations
│   ├── versions/
│   │   └── 001_initial_schema.py
│   └── env.py
├── tests/                   # Pytest test suite
│   ├── conftest.py
│   ├── test_webhook.py
│   ├── test_services.py
│   └── test_admin_api.py
├── Dockerfile               # Multi-stage container build with non-root user
├── docker-compose.yml       # postgres, redis, api, worker
├── pyproject.toml
└── .env.example
```

---

## Local Setup

### 1. Configuration
```bash
cd backend
cp .env.example .env
```
Fill in `.env` with your credentials:
```ini
DATABASE_URL=postgresql+asyncpg://postgres:postgrespassword@localhost:5432/whatsapp_agent
REDIS_URL=redis://localhost:6379/0
WHATSAPP_TOKEN=your_permanent_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_APP_SECRET=your_app_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
```

### 2. Run Database Migrations
```bash
alembic upgrade head
```

### 3. Start API Service
```bash
uvicorn backend.app.main:app --reload --port 8000
```

### 4. Start Background Worker
```bash
arq backend.app.worker.settings.WorkerSettings
```

---

## Docker Compose Setup

Run the complete backend stack (Postgres, Redis, API, and Worker):
```bash
docker compose up -d
```

---

## Running Backend Tests

```bash
pytest -c backend/pyproject.toml backend/tests -q
```
Runs all 14 tests against an in-memory SQLite database and FakeRedis.
