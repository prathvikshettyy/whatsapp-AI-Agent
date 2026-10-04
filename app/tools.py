"""Tool schemas and dispatch implementations for Claude.

Supports read-only queries and side-effect tools requiring explicit user confirmation.
"""

from typing import Any, Dict, List, Optional

# Definitions in Anthropic Claude tool specification format
TOOL_DEFINITIONS: List[Dict[str, Any]] = [
    {
        "name": "search_knowledge_base",
        "description": "Search the knowledge base for business hours, return policy, delivery coverage, and common inquiries.",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Keywords or question to search the knowledge base",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_order_status",
        "description": "Retrieve current tracking and fulfillment status for a given order ID.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The unique order identifier (e.g., ORD-1029)",
                }
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "calculate_shipping_quote",
        "description": "Calculate estimated shipping cost and delivery days based on destination postal code and weight.",
        "input_schema": {
            "type": "object",
            "properties": {
                "postal_code": {
                    "type": "string",
                    "description": "Destination postal/zip code",
                },
                "weight_kg": {
                    "type": "number",
                    "description": "Package weight in kilograms",
                },
            },
            "required": ["postal_code", "weight_kg"],
        },
    },
    {
        "name": "schedule_appointment",
        "description": "Schedule a customer consultation or support callback appointment.",
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {
                    "type": "string",
                    "description": "Requested date (YYYY-MM-DD)",
                },
                "time_slot": {
                    "type": "string",
                    "description": "Requested time slot (e.g., 10:00 AM, 02:30 PM)",
                },
                "topic": {
                    "type": "string",
                    "description": "Brief description of the consultation topic",
                },
            },
            "required": ["date", "time_slot"],
        },
    },
    {
        "name": "cancel_order",
        "description": "Cancel an order and void shipment. SENSITIVE: requires explicit confirmation from user.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to cancel",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for cancellation",
                },
            },
            "required": ["order_id"],
        },
    },
    {
        "name": "initiate_refund",
        "description": "Initiate refund for a transaction or order. SENSITIVE: requires explicit user confirmation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_id": {
                    "type": "string",
                    "description": "The order ID to refund",
                },
                "amount": {
                    "type": "number",
                    "description": "Refund amount in USD",
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for refund",
                },
            },
            "required": ["order_id", "amount"],
        },
    },
]

# Sensitive tools that require user confirmation before executing side effects
SENSITIVE_TOOLS = {"cancel_order", "initiate_refund"}

# Mock database records for demonstration
MOCK_ORDERS: Dict[str, Dict[str, Any]] = {
    "ORD-1029": {
        "status": "In Transit",
        "carrier": "FedEx",
        "tracking_number": "TRK983726154",
        "estimated_delivery": "Tomorrow by 5:00 PM",
        "items": ["Wireless Noise-Cancelling Headphones (1x)"],
        "total": 149.99,
    },
    "ORD-2045": {
        "status": "Processing",
        "carrier": "USPS",
        "tracking_number": "Pending",
        "estimated_delivery": "In 3 business days",
        "items": ["Ergonomic Mechanical Keyboard (1x)"],
        "total": 89.50,
    },
}

MOCK_KB: Dict[str, str] = {
    "hours": "Our customer support team is available Monday through Friday from 9:00 AM to 6:00 PM EST.",
    "return": "We offer a 30-day no-questions-asked return policy on all unused items in original packaging.",
    "shipping": "Standard shipping takes 3-5 business days. Express shipping takes 1-2 business days. Free shipping on orders over $50.",
    "warranty": "All electronics are covered by a 1-year limited manufacturer warranty.",
}


async def execute_tool(
    name: str,
    args: Dict[str, Any],
    wa_id: str,
    confirmed: bool = False,
) -> Dict[str, Any]:
    """
    Execute tool by name with arguments.
    If the tool has side effects and confirmed is False, returns a confirmation requirement.
    """
    if name in SENSITIVE_TOOLS and not confirmed:
        return {
            "status": "requires_user_confirmation",
            "action": name,
            "params": args,
            "message": (
                f"Action *{name}* involves financial or order changes. "
                "Please ask the user to explicitly confirm before proceeding."
            ),
        }

    if name == "search_knowledge_base":
        query = args.get("query", "").lower()
        matched = []
        for key, text in MOCK_KB.items():
            if key in query or any(word in text.lower() for word in query.split()):
                matched.append(text)
        if not matched:
            matched.append(
                "No exact FAQ entry matched. Our human support team is also available during business hours."
            )
        return {"results": matched}

    elif name == "check_order_status":
        order_id = str(args.get("order_id", "")).strip().upper()
        if order_id in MOCK_ORDERS:
            return {"order": MOCK_ORDERS[order_id]}
        return {
            "error": f"Order {order_id} not found. Please verify the ID format (e.g. ORD-1029)."
        }

    elif name == "calculate_shipping_quote":
        postal_code = args.get("postal_code", "")
        weight = float(args.get("weight_kg", 1.0))
        base_rate = 5.99
        cost = round(base_rate + (weight * 1.50), 2)
        return {
            "postal_code": postal_code,
            "weight_kg": weight,
            "estimated_cost_usd": cost,
            "delivery_window": "2-4 business days",
        }

    elif name == "schedule_appointment":
        date = args.get("date")
        time_slot = args.get("time_slot")
        topic = args.get("topic", "General Inquiry")
        return {
            "status": "confirmed",
            "appointment_id": "APT-8821",
            "date": date,
            "time_slot": time_slot,
            "topic": topic,
        }

    elif name == "cancel_order":
        order_id = str(args.get("order_id", "")).strip().upper()
        reason = args.get("reason", "Customer requested cancellation")
        if order_id in MOCK_ORDERS:
            MOCK_ORDERS[order_id]["status"] = "Cancelled"
            return {
                "status": "cancelled",
                "order_id": order_id,
                "reason": reason,
                "confirmation": f"Order {order_id} has been successfully cancelled.",
            }
        return {"error": f"Order {order_id} not found."}

    elif name == "initiate_refund":
        order_id = str(args.get("order_id", "")).strip().upper()
        amount = args.get("amount", 0.0)
        reason = args.get("reason", "Customer refund")
        return {
            "status": "refund_initiated",
            "refund_id": "RFND-9902",
            "order_id": order_id,
            "amount_usd": amount,
            "reason": reason,
            "message": f"Refund of ${amount:.2f} initiated for order {order_id}.",
        }

    return {"error": f"Unknown tool: {name}"}
