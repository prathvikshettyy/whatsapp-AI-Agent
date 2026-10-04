"""Claude AI agent loop with tool dispatch, history loading, and WhatsApp formatting."""

import base64
import json
import logging
from typing import Any, Dict, List, Optional
from anthropic import AsyncAnthropic

from app.config import settings
from app.store import RedisStore, store as default_store
from app.tools import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an intelligent, helpful, and concise customer support AI agent communicating with users on WhatsApp for our business.

CRITICAL WHATSAPP FORMATTING RULES:
1. WhatsApp DOES NOT support Markdown headings (# Heading), HTML tags, or Markdown tables (| col |). NEVER use them.
2. WhatsApp only supports the following text styling:
   - *bold* (asterisks on both sides)
   - _italics_ (underscores on both sides)
   - ~strikethrough~ (tildes on both sides)
   - ```monospace``` (triple backticks)
3. Keep answers clean, friendly, and easily scannable for mobile screens. Use short bullet points with emojis or hyphens rather than long paragraphs.
4. Keep replies within standard conversational lengths.
5. If the user asks about an order, appointments, or policies, use the available tools to provide real, accurate details.
6. SAFETY RULE: Actions with irreversible side effects (such as canceling orders, initiating refunds, or processing payments) require explicit user confirmation before executing. If the tool indicates user confirmation is required, ask the user clearly to confirm with the details.
"""


class WhatsAppAgent:
    """Manages conversational agent reasoning with Anthropic Claude."""

    def __init__(
        self,
        anthropic_client: Optional[AsyncAnthropic] = None,
        store: Optional[RedisStore] = None,
    ):
        self._client = anthropic_client
        self.store = store or default_store

    def _get_anthropic_client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def process_user_turn(
        self,
        wa_id: str,
        user_text: Optional[str] = None,
        image_bytes: Optional[bytes] = None,
        image_mime: Optional[str] = None,
        is_confirmed_action: bool = False,
    ) -> str:
        """
        Process incoming user turn:
        1. Formats content (supports text and multimodal image).
        2. Retrieves chat history from Redis.
        3. Loops with Claude tool calls (up to MAX_TOOL_ITERATIONS).
        4. Saves turns to Redis.
        5. Returns final WhatsApp-formatted text.
        """
        client = self._get_anthropic_client()

        # Build message content block for the current user turn
        current_content: List[Dict[str, Any]] = []

        if image_bytes and image_mime:
            b64_img = base64.b64encode(image_bytes).decode("utf-8")
            current_content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": image_mime,
                    "data": b64_img,
                },
            })

        if user_text:
            current_content.append({
                "type": "text",
                "text": user_text,
            })
        elif not image_bytes:
            current_content.append({
                "type": "text",
                "text": "[Empty or unsupported media message]",
            })

        # Load conversation history from Redis
        history = await self.store.get_history(wa_id, settings.MAX_HISTORY_TURNS)
        messages: List[Dict[str, Any]] = list(history)

        # Append current user message
        messages.append({
            "role": "user",
            "content": current_content if len(current_content) > 1 or (image_bytes and image_mime) else (user_text or ""),
        })

        iteration = 0
        final_reply = ""

        while iteration < settings.MAX_TOOL_ITERATIONS:
            iteration += 1

            try:
                response = await client.messages.create(
                    model=settings.CLAUDE_MODEL,
                    system=SYSTEM_PROMPT,
                    messages=messages,
                    tools=TOOL_DEFINITIONS,
                    max_tokens=1024,
                )
            except Exception as e:
                logger.error(f"Claude API call failed: {e}")
                return "We are currently experiencing a brief technical issue. Please try again in a few moments."

            # Append assistant response to messages for tool conversation tracking
            messages.append({
                "role": "assistant",
                "content": response.content,
            })

            # Check if tools were invoked
            tool_calls = [c for c in response.content if getattr(c, "type", None) == "tool_use"]

            if not tool_calls or response.stop_reason != "tool_use":
                # Extract text responses
                text_blocks = [
                    c.text for c in response.content if getattr(c, "type", None) == "text"
                ]
                final_reply = "\n".join(text_blocks).strip()
                break

            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                tool_name = tool_call.name
                tool_input = tool_call.input
                tool_id = tool_call.id

                logger.info(f"Executing tool {tool_name} with ID {tool_id}")
                result = await execute_tool(
                    name=tool_name,
                    args=tool_input,
                    wa_id=wa_id,
                    confirmed=is_confirmed_action,
                )

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(result),
                })

            messages.append({
                "role": "user",
                "content": tool_results,
            })

        if not final_reply:
            final_reply = "I have processed your request. Is there anything else I can help you with?"

        # Persist conversation to Redis store
        # For history storage, keep concise representation
        await self.store.add_turn(
            wa_id=wa_id,
            role="user",
            content=user_text if user_text else "[Image / Media]",
        )
        await self.store.add_turn(
            wa_id=wa_id,
            role="assistant",
            content=final_reply,
        )

        return final_reply


agent = WhatsAppAgent()
