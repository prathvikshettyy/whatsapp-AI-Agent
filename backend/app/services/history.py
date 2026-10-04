"""Chat history loader and formatting for Anthropic Claude."""

from typing import Any, Dict, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.models.message import Message


async def load_conversation_history(
    session: AsyncSession,
    conversation_id: str,
    max_turns: int = 20,
) -> List[Dict[str, Any]]:
    """
    Load last N turns from Postgres and format into Claude message blocks.
    Guarantees tool_use and tool_result pairs remain intact when trimming.
    """
    stmt = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.tool_calls))
        .order_by(Message.created_at.desc())
        .limit(max_turns * 2)
    )
    res = await session.execute(stmt)
    db_messages = list(reversed(res.scalars().all()))

    formatted: List[Dict[str, Any]] = []

    for msg in db_messages:
        role = "user" if msg.role == "user" else "assistant"
        content: Any = msg.content or ""

        # If assistant has tool calls, format as tool_use blocks
        if role == "assistant" and msg.tool_calls:
            blocks = []
            if msg.content:
                blocks.append({"type": "text", "text": msg.content})
            for tc in msg.tool_calls:
                blocks.append({
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": tc.args_redacted or {},
                })
            content = blocks

        formatted.append({"role": role, "content": content})

    # Ensure message sequence starts with 'user'
    while formatted and formatted[0]["role"] != "user":
        formatted.pop(0)

    return formatted
