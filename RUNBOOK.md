# Operations Runbook

Operational procedures, incident recovery workflows, and maintenance guides for the WhatsApp AI Agent platform.

---

## 1. Health Checks & Monitoring

- **Service Health Endpoint**: `GET /health`
  - Validates PostgreSQL database connectivity (`SELECT 1`).
  - Validates Redis ping.
  - Returns `{"status": "healthy", "database": "connected", "redis": "connected"}`.
- **Queue Lag**:
  - Monitor arq job queue depth in Redis: `LLEN arq:queue`.
  - Normal depth: < 50 jobs. If depth > 200, scale worker instances.

---

## 2. Common Incident Playbooks

### A. Webhook Signature Verification Failures (403 Forbidden)
- **Symptom**: Logs display `webhook_invalid_signature`.
- **Cause**: `WHATSAPP_APP_SECRET` does not match Meta App Secret in Meta Developer Dashboard.
- **Resolution**:
  1. Open Meta App Dashboard > Settings > Basic > App Secret.
  2. Copy App Secret into `WHATSAPP_APP_SECRET` in environment.
  3. Restart API service.

### B. Messages Failing to Deliver Outside 24h Window
- **Symptom**: Graph API returns error code `131047` (Re-engagement message).
- **Cause**: User's last incoming message occurred >24 hours ago.
- **Resolution**:
  1. Staff must select an approved Meta Message Template in dashboard composer.
  2. Free-text replies will unlock once the customer replies to the template.

### C. Rotating WhatsApp Permanent System User Token
1. Meta Business Manager > Business Settings > System Users.
2. Select your System User > Generate Token.
3. Select WhatsApp permissions (`whatsapp_business_messaging`, `whatsapp_business_management`).
4. Update `WHATSAPP_TOKEN` in production secret manager.
5. Deploy updated container.

---

## 3. Database Backup & Restore

### PostgreSQL Backup
```bash
pg_dump -U postgres -d whatsapp_agent -Fc -f /backups/backup_$(date +%Y%m%d).dump
```

### PostgreSQL Restore Test
```bash
pg_restore -U postgres -d whatsapp_agent_test /backups/backup_20261004.dump
```
