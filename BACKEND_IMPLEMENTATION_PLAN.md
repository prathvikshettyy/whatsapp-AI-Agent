# Backend Implementation Plan

Stack: Python 3.12, FastAPI, Postgres (SQLAlchemy 2 + Alembic), Redis, arq (worker), Anthropic SDK, httpx, pydantic-settings, structlog, pytest.

Timeline: ~15 working days solo. Phases 1-5 = working bot. Phases 6-7 = admin API for dashboard.

## Folder structure

```
backend/
  app/
    main.py                 # FastAPI app, router include, lifespan
    config.py               # pydantic-settings
    db.py                   # engine, session
    models/                 # SQLAlchemy models
      contact.py conversation.py message.py tool_call.py
      kb_doc.py setting.py staff_user.py audit_log.py
    schemas/                # pydantic request/response
    api/
      webhook.py            # GET/POST /webhook
      auth.py
      conversations.py
      kb.py
      settings.py
      stream.py             # SSE
      analytics.py
      deps.py               # auth, db session deps
    services/
      whatsapp.py           # send, media, mark read, templates
      agent.py              # Claude loop
      tools/
        registry.py         # schema + dispatch
      history.py            # load, trim, format for Claude
      ratelimit.py
      handoff.py
      media.py              # download, transcribe
      events.py             # Redis pub/sub for SSE
    worker/
      tasks.py              # process_inbound, send_template
      settings.py           # arq WorkerSettings
    security/
      signature.py          # X-Hub-Signature-256
      passwords.py jwt.py
  alembic/
  tests/
  Dockerfile
  docker-compose.yml        # api, worker, postgres, redis
  pyproject.toml
  .env.example
```

## Schema

```sql
contacts(id, wa_id UNIQUE, name, opted_out BOOL, created_at)
conversations(id, contact_id FK, status ENUM('bot','human','closed'),
              last_user_msg_at, assigned_to FK NULL, created_at)
messages(id, wa_msg_id UNIQUE NULL, conversation_id FK, role ENUM('user','bot','staff'),
         content TEXT, media_type, media_ref, tokens_in, tokens_out, created_at)
tool_calls(id, message_id FK, name, args_redacted JSONB, status, latency_ms, created_at)
kb_docs(id, title, body, updated_at)
settings(id, system_prompt, model, rate_limit_per_min, handoff_keyword, version, created_by, created_at)
staff_users(id, email UNIQUE, password_hash, role ENUM('admin','agent'))
audit_log(id, actor_id, action, target, meta JSONB, created_at)
```

Indexes: `messages(conversation_id, created_at)`, `conversations(status, last_user_msg_at DESC)`, `contacts(wa_id)`.
