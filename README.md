# WhatsApp AI Agent

Production-ready AI agent on WhatsApp using the official WhatsApp Business Platform (Cloud API) and Claude.

**Stack**: Python 3.12+, FastAPI, Anthropic Claude SDK, Redis, httpx.

---

## Architecture & Flow

```
User -> WhatsApp -> Meta Cloud API -> POST /webhook (FastAPI)
                                          |
                                  verify signature, dedupe, enqueue
                                          |
                                      worker
                                          |
                  load history (Redis) -> Claude API + tools -> loop until text
                                          |
                  POST graph.facebook.com/<PHONE_NUMBER_ID>/messages -> User
```

1. **Meta Webhook Ingestion**: Meta sends message payloads to `POST /webhook`.
2. **Signature Verification**: Validates `X-Hub-Signature-256` using HMAC-SHA256 with `WHATSAPP_APP_SECRET`.
3. **Deduplication**: Every incoming message ID is deduped in Redis with `SET NX EX 86400`. Retries from Meta are acknowledged immediately with HTTP 200 without duplicate execution.
4. **Rate Limiting & Safety**: Sliding-window rate limiting per `wa_id`. Opt-out ("stop") and Human Handoff ("agent") requests are intercepted before calling LLM.
5. **Tool Loop & Confirmation**: Claude reasons with available tools (up to 8 iterations). Side-effect tools (cancellations, refunds) require explicit confirmation.
6. **WhatsApp Formatting & Dispatch**: Output respects WhatsApp's styling rules (`*bold*`, `_italics_`, `~strike~`, ```mono```) and automatically splits messages exceeding 4096 characters.

---

## Project Layout

```
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, webhook verification & ingestion routes
│   ├── whatsapp.py      # WhatsApp Cloud API client (send, mark read, media, split)
│   ├── agent.py         # Claude reasoning loop + multi-modal + tool dispatch
│   ├── tools.py         # Tool schemas, implementations & side-effect gates
│   ├── store.py         # Redis state: history, dedupe, rate-limit, handoff, opt-out
│   ├── config.py        # Pydantic environment configuration
│   └── worker.py        # Async message processing & Redis queue worker
├── tests/
│   ├── __init__.py
│   ├── conftest.py      # Fixtures with FakeRedis and mock configs
│   ├── test_webhook.py  # GET/POST webhook verification and dedupe tests
│   ├── test_store.py    # Redis store unit tests
│   ├── test_whatsapp.py # API client, message chunking, phone masking tests
│   └── test_worker_and_agent.py # Tool loop, human handoff, opt-out tests
├── .env.example
├── Dockerfile
├── requirements.txt
└── README.md
```

---

## Prerequisites

- Meta Developer account with WhatsApp Business Cloud API app.
- Meta Phone Number ID and System User Permanent Access Token.
- Anthropic API Key (Claude).
- Redis instance (local, Docker, or managed like Upstash / Redis Cloud).
- Public HTTPS webhook URL (e.g. ngrok or Cloudflare Tunnel for local development).

---

## Setup & Local Run

### 1. Clone & create virtual environment
```bash
git clone <repo> && cd "whatsapp agent"
python -m venv .venv
source .venv/bin/activate    # On Windows: .\.venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables
```bash
cp .env.example .env
```
Fill in the values in `.env`:
```ini
WHATSAPP_TOKEN=your_permanent_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_VERIFY_TOKEN=your_custom_webhook_verify_token
WHATSAPP_APP_SECRET=your_meta_app_secret
ANTHROPIC_API_KEY=your_anthropic_api_key
CLAUDE_MODEL=claude-3-5-sonnet-latest
REDIS_URL=redis://localhost:6379/0
MAX_HISTORY_TURNS=20
RATE_LIMIT_PER_MIN=10
```

### 3. Run FastAPI Application
```bash
uvicorn app.main:app --reload --port 8000
```

### 4. Expose Webhook via ngrok
```bash
ngrok http 8000
```
Use `https://<your-ngrok-subdomain>.ngrok-free.app/webhook` as your Webhook Callback URL in Meta Developer Dashboard.

---

## Meta Dashboard Configuration

1. Go to **Meta for Developers** > **WhatsApp** > **Configuration** > **Webhook**.
2. Click **Edit**:
   - **Callback URL**: `https://<your-host>/webhook`
   - **Verify token**: The exact value set in `WHATSAPP_VERIFY_TOKEN`.
3. Click **Verify and Save**.
4. In Webhook fields, click **Manage** and subscribe to: `messages`.
5. Under **API Setup**, add your personal phone number as a recipient to send and receive test messages.

---

## Webhook Contract

### `GET /webhook`
Meta verification challenge.
- Query parameters: `hub.mode`, `hub.verify_token`, `hub.challenge`.
- If `hub.verify_token` matches `WHATSAPP_VERIFY_TOKEN` and `hub.mode == "subscribe"`, returns `hub.challenge` in plain text with HTTP 200.
- Otherwise returns HTTP 403 Forbidden.

### `POST /webhook`
Meta event delivery.
1. Validates `X-Hub-Signature-256` header matches `sha256=` + HMAC-SHA256(`WHATSAPP_APP_SECRET`, raw_body).
2. Parses `entry[].changes[].value.messages[]` (skips delivery/read `statuses` updates).
3. Dedupes on `message.id` via Redis (`SET NX EX 86400`).
4. Enqueues background message processing.
5. Returns HTTP 200 OK immediately to satisfy Meta's fast acknowledgement policy.

---

## Safety & Compliance Features

- **Webhook Signature Security**: Verifies HMAC-SHA256 signature on every incoming payload.
- **Opt-Out Compliance ("STOP")**: Automatically processes unsubscribe requests ("stop", "unsubscribe", "cancel"), sets persistent opt-out in Redis, and prevents automated messages until the user replies "START".
- **Human Handoff ("AGENT")**: When a user asks for a representative ("agent", "human", "support"), the bot marks the conversation for human intervention, notifies the user, and pauses bot replies. Send "BOT" to resume.
- **Side-Effect Confirmation Gate**: Sensitive operations (e.g. canceling orders, processing refunds) require explicit confirmation before execution.
- **PII Protection**: Phone numbers are masked in all logs (`155****4567`). Never logs API tokens or raw authorization headers.
- **Rate Limiting**: Sliding window rate limiter in Redis per WhatsApp phone number (`wa_id`).

---

## Deploy with Docker

```bash
docker build -t whatsapp-agent .
docker run --env-file .env -p 8000:8000 whatsapp-agent
```

For production deployments (Railway, Render, Fly.io, or AWS ECS), you can run:
- **Web service**: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- **Worker service**: `python -m app.worker` (listens on Redis queue `wa:incoming_messages_queue`)

---

## Running Tests

Run the test suite with pytest:
```bash
pytest -q
```
All 22 unit and integration tests run in an isolated environment with `fakeredis` and mocked HTTP transports.

---

## License

MIT
