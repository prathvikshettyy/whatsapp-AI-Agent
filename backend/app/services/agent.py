"""Claude Agent reasoning loop with tool calling and prompt formatting."""

import json
import time
from typing import Any, Dict, List, Optional, Tuple
from anthropic import AsyncAnthropic
import structlog

from backend.app.config import settings
from backend.app.services.tools.registry import TOOLS_SCHEMA, run_tool

logger = structlog.get_logger(__name__)

SYSTEM_PROMPT = """You are a helpful and concise customer support AI assistant communicating with users on WhatsApp.

WHATSAPP FORMATTING GUIDELINES:
1. WhatsApp DOES NOT support Markdown headings (# Heading) or Markdown tables (| col |). NEVER use them.
2. WhatsApp only supports:
   - *bold*
   - _italics_
   - ~strikethrough~
   - ```monospace```
3. Keep replies clear, friendly, and structured with short bullet points for mobile screens.
4. Keep answers concise.
5. If the user asks for order tracking, consultation scheduling, or cancellations, execute the appropriate tool.
6. Sensitive operations (cancellations, refunds) require asking the user to confirm before final execution.
"""


class AgentLoopExceeded(Exception):
    pass


class AgentService:
    def __init__(self, client: Optional[AsyncAnthropic] = None):
        self._client = client

    def _get_client(self) -> AsyncAnthropic:
        if self._client is None:
            self._client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        return self._client

    async def run(
        self,
        messages: List[Dict[str, Any]],
        wa_id: str,
        system_prompt: Optional[str] = None,
        is_confirmed: bool = False,
    ) -> Tuple[str, List[Dict[str, Any]], int, int]:
        """
        Run Claude reasoning loop.
        Returns: (final_reply_text, executed_tools_audit, tokens_in, tokens_out)
        """
        client = self._get_client()
        sys_prompt = system_prompt or SYSTEM_PROMPT
        total_tokens_in = 0
        total_tokens_out = 0
        tool_audits: List[Dict[str, Any]] = []

        for step in range(settings.MAX_STEPS):
            try:
                resp = await client.messages.create(
                    model=settings.CLAUDE_MODEL,
                    system=sys_prompt,
                    messages=messages,
                    tools=TOOLS_SCHEMA,
                    max_tokens=1024,
                )
            except Exception as e:
                logger.error("claude_api_error", step=step, error=str(e))
                return (
                    "We are temporarily experiencing technical difficulties. A human agent will assist you shortly.",
                    tool_audits,
                    total_tokens_in,
                    total_tokens_out,
                )

            total_tokens_in += getattr(resp.usage, "input_tokens", 0)
            total_tokens_out += getattr(resp.usage, "output_tokens", 0)

            # Track assistant turn
            messages.append({"role": "assistant", "content": resp.content})

            # Check for tool invocations
            tool_calls = [c for c in resp.content if getattr(c, "type", None) == "tool_use"]

            if not tool_calls or resp.stop_reason != "tool_use":
                # Extract text blocks
                text_blocks = [c.text for c in resp.content if getattr(c, "type", None) == "text"]
                final_text = "\n".join(text_blocks).strip()
                return final_text, tool_audits, total_tokens_in, total_tokens_out

            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                start_t = time.time()
                result = await run_tool(
                    name=tool_call.name,
                    args=tool_call.input,
                    wa_id=wa_id,
                    confirmed=is_confirmed,
                )
                latency = int((time.time() - start_t) * 1000)

                tool_audits.append({
                    "name": tool_call.name,
                    "args": tool_call.input,
                    "status": result.get("status", "ok"),
                    "result": result,
                    "latency_ms": latency,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": json.dumps(result),
                })

            messages.append({"role": "user", "content": tool_results})

        raise AgentLoopExceeded("Exceeded maximum tool loop steps")


agent_service = AgentService()
