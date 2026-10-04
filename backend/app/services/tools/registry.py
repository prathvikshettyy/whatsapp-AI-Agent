"""Tool registry and dispatcher for Anthropic Claude."""

import json
from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field

# Anthropic Claude tool schemas
TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "name": "check_order_status",
        "description": "Retrieve current tracking and fulfillment status for a given order ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order reference code (e.g. ORD-1029)"}
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "schedule_appointment",
        "description": "Schedule a consultation or customer support callback appointment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Requested date (YYYY-MM-DD)"},
                "time_slot": {"type": "string", "description": "Requested time (e.g. 10:00 AM)"},
                "topic": {"type": "string", "description": "Reason for meeting"},
            },
            "required": ["date", "time_slot"],
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an order and void shipment. SENSITIVE: Requires explicit user confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "The order ID to cancel"},
                "reason": {"type": "string", "description": "Reason for cancellation"},
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "initiate_refund",
        "description": "Initiate refund for a transaction or order. SENSITIVE: Requires user confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "Order ID to refund"},
                "amount": {"type": "number", "description": "Refund amount in USD"},
                "reason": {"type": "string", "description": "Reason for refund"},
            },
            "required": ["order_id", "amount"],
        },
    },
    {
        "name": "request_human",
        "description": "Request human staff agent intervention when the customer asks for a human.",
        "input_schema": {
            "type": "object",
            "properties": {
                "reason": {"type": "string", "description": "Why human assistance is required"}
            },
            "required": ["reason"],
        },
    },
]

SENSITIVE_TOOLS = {"cancel_order", "initiate_refund"}

MOCK_ORDERS = {
    "ORD-1029": {"status": "In Transit", "carrier": "FedEx", "tracking": "TRK983726154", "eta": "Tomorrow by 5:00 PM"},
    "ORD-2045": {"status": "Processing", "carrier": "USPS", "tracking": "Pending", "eta": "3 business days"},
}


async def run_tool(name: str, args: Dict[str, Any], wa_id: str, confirmed: bool = False) -> Dict[str, Any]:
    """Execute tool with confirmation gating and server-side authorization."""
    if name in SENSITIVE_TOOLS and not confirmed:
        return {
            "status": "requires_user_confirmation",
            "action": name,
            "params": args,
            "message": f"Action *{name}* involves changes. Ask the user to confirm before proceeding.",
        }

    if name == "check_order_status":
        order_id = str(args.get("order_id", "")).strip().upper()
        if order_id in MOCK_ORDERS:
            return {"order": MOCK_ORDERS[order_id]}
        return {"error": f"Order {order_id} not found."}

    elif name == "schedule_appointment":
        return {
            "status": "confirmed",
            "appointment_id": "APT-8821",
            "date": args.get("date"),
            "time_slot": args.get("time_slot"),
        }

    elif name == "cancel_order":
        order_id = str(args.get("order_id", "")).strip().upper()
        if order_id in MOCK_ORDERS:
            MOCK_ORDERS[order_id]["status"] = "Cancelled"
            return {"status": "cancelled", "order_id": order_id}
        return {"error": f"Order {order_id} not found."}

    elif name == "initiate_refund":
        return {
            "status": "refund_initiated",
            "order_id": args.get("order_id"),
            "amount": args.get("amount"),
        }

    elif name == "request_human":
        return {
            "status": "human_requested",
            "message": "Human agent alerted to take over.",
        }

    return {"error": f"Unknown tool: {name}"}
