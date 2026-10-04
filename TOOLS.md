# WhatsApp Agent Tools Specification

Detailed reference of all tools exposed to Anthropic Claude in the WhatsApp agent loop.

---

## 1. Tool Summary

| Tool Name | Type | Sensitive? | Purpose |
|---|---|---|---|
| `check_order_status` | Read-only | No | Lookup shipment status, carrier, ETA by `order_id` |
| `schedule_appointment` | Read-write | No | Book support consultation by date & time slot |
| `calculate_shipping_quote` | Read-only | No | Calculate shipping fees and estimated delivery days |
| `cancel_order` | Side-effect | **Yes** | Cancels active order. Requires user confirmation |
| `initiate_refund` | Financial | **Yes** | Triggers payment refund. Requires user confirmation |
| `request_human` | Escalation | No | Flags conversation for human staff takeover |

---

## 2. Tool Definitions

### `check_order_status`
```json
{
  "name": "check_order_status",
  "description": "Retrieve current tracking and fulfillment status for a given order ID.",
  "input_schema": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "Order reference code (e.g. ORD-1029)"
      }
    },
    "required": ["order_id"]
  }
}
```

### `schedule_appointment`
```json
{
  "name": "schedule_appointment",
  "description": "Schedule a customer consultation or support callback appointment.",
  "input_schema": {
    "type": "object",
    "properties": {
      "date": {
        "type": "string",
        "description": "Requested date (YYYY-MM-DD)"
      },
      "time_slot": {
        "type": "string",
        "description": "Requested time slot (e.g. 10:00 AM)"
      },
      "topic": {
        "type": "string",
        "description": "Topic or inquiry description"
      }
    },
    "required": ["date", "time_slot"]
  }
}
```

### `cancel_order` (Gated)
```json
{
  "name": "cancel_order",
  "description": "Cancel an order and void shipment. SENSITIVE: requires explicit confirmation from user.",
  "input_schema": {
    "type": "object",
    "properties": {
      "order_id": {
        "type": "string",
        "description": "The order ID to cancel"
      },
      "reason": {
        "type": "string",
        "description": "Reason for cancellation"
      }
    },
    "required": ["order_id"]
  }
}
```

---

## 3. Server-Side Safety & Authorization Rules

1. **Authorization**: Tools never trust client-supplied user IDs. The server binds `wa_id` directly from the authenticated WhatsApp webhook payload.
2. **Confirmation Gate**: When a sensitive tool (`cancel_order`, `initiate_refund`) is invoked without confirmation (`confirmed=False`), the dispatcher intercepts the call and returns:
   ```json
   {
     "status": "requires_user_confirmation",
     "action": "cancel_order",
     "params": { "order_id": "ORD-1029" },
     "message": "Action cancel_order involves changes. Ask user to confirm."
   }
   ```
   Claude presents the confirmation question to the customer. When the user replies "CONFIRM" or "YES", the pending action is retrieved from Redis and executed with `confirmed=True`.
