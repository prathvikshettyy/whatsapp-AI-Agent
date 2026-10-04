"""WhatsApp Business Cloud API client.

Handles sending text messages (with auto-splitting >4096 chars),
marking incoming messages as read, and fetching/downloading media (images/audio).
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


def mask_phone_number(phone: str) -> str:
    """Mask phone number for safe logging (never log full phone numbers)."""
    if not phone:
        return "unknown"
    cleaned = re.sub(r"[^\d+]", "", phone)
    if len(cleaned) <= 4:
        return "****"
    return f"{cleaned[:3]}****{cleaned[-4:]}"


def split_message(text: str, max_length: int = 4096) -> List[str]:
    """
    Split text into chunks not exceeding max_length.
    Prefers splitting at paragraphs, then line breaks, then sentence boundaries, then spaces.
    """
    if not text:
        return [""]
    if len(text) <= max_length:
        return [text]

    chunks: List[str] = []
    remaining = text.strip()

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        # Look for split point within max_length
        split_idx = -1
        # Try paragraph split
        para_idx = remaining.rfind("\n\n", 0, max_length)
        if para_idx != -1 and para_idx >= max_length // 3:
            split_idx = para_idx + 2
        else:
            # Try single line break
            line_idx = remaining.rfind("\n", 0, max_length)
            if line_idx != -1 and line_idx >= max_length // 3:
                split_idx = line_idx + 1
            else:
                # Try sentence end
                period_idx = max(
                    remaining.rfind(". ", 0, max_length),
                    remaining.rfind("! ", 0, max_length),
                    remaining.rfind("? ", 0, max_length),
                )
                if period_idx != -1 and period_idx >= max_length // 3:
                    split_idx = period_idx + 2
                else:
                    # Try space
                    space_idx = remaining.rfind(" ", 0, max_length)
                    if space_idx != -1:
                        split_idx = space_idx + 1
                    else:
                        # Hard split
                        split_idx = max_length

        chunk = remaining[:split_idx].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_idx:].strip()

    return chunks


class WhatsAppClient:
    """Async client for WhatsApp Cloud API."""

    def __init__(
        self,
        token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        base_url: Optional[str] = None,
        version: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.token = token or settings.WHATSAPP_TOKEN
        self.phone_number_id = phone_number_id or settings.WHATSAPP_PHONE_NUMBER_ID
        self.base_url = (base_url or settings.GRAPH_API_BASE_URL).rstrip("/")
        self.version = version or settings.GRAPH_API_VERSION
        self._http_client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client

    async def close(self) -> None:
        if self._http_client is not None and not self._http_client.is_closed:
            await self._http_client.aclose()
            self._http_client = None

    @property
    def messages_endpoint(self) -> str:
        return f"{self.base_url}/{self.version}/{self.phone_number_id}/messages"

    @property
    def default_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def send_text_message(
        self,
        to: str,
        text: str,
        reply_to_message_id: Optional[str] = None,
        preview_url: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Send a text message to a WhatsApp user.
        Splits automatically if message exceeds 4096 chars.
        """
        client = await self._get_client()
        chunks = split_message(text, settings.MAX_MESSAGE_LENGTH)
        responses: List[Dict[str, Any]] = []

        logger.info(
            f"Sending {len(chunks)} message chunk(s) to recipient {mask_phone_number(to)}"
        )

        for i, chunk in enumerate(chunks):
            payload: Dict[str, Any] = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {
                    "preview_url": preview_url,
                    "body": chunk,
                },
            }

            # Link reply context only to the first chunk if specified
            if reply_to_message_id and i == 0:
                payload["context"] = {"message_id": reply_to_message_id}

            try:
                resp = await client.post(
                    self.messages_endpoint,
                    headers=self.default_headers,
                    json=payload,
                )
                resp.raise_for_status()
                data = resp.json()
                responses.append(data)
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"WhatsApp send message failed with status {e.response.status_code}: {e.response.text}"
                )
                raise
            except Exception as e:
                logger.error(f"WhatsApp send message network error: {e}")
                raise

        return responses

    async def mark_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark incoming message as read."""
        client = await self._get_client()
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }

        try:
            resp = await client.post(
                self.messages_endpoint,
                headers=self.default_headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            # Marking read is best-effort, log warning but don't disrupt the flow
            logger.warning(f"Failed to mark message {message_id} as read: {e}")
            return {"success": False, "error": str(e)}

    async def get_media_url(self, media_id: str) -> Tuple[str, str]:
        """
        Retrieve media download URL and mime type from Meta Graph API.
        Returns: (media_url, mime_type)
        """
        client = await self._get_client()
        endpoint = f"{self.base_url}/{self.version}/{media_id}"
        headers = {"Authorization": f"Bearer {self.token}"}

        resp = await client.get(endpoint, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        url = data.get("url", "")
        mime_type = data.get("mime_type", "application/octet-stream")
        return url, mime_type

    async def download_media(self, media_url: str) -> bytes:
        """
        Download media binary bytes using Meta bearer token.
        Meta requires Bearer Authorization and a standard User-Agent header.
        """
        client = await self._get_client()
        headers = {
            "Authorization": f"Bearer {self.token}",
            "User-Agent": "WhatsAppAIClient/1.0",
        }
        resp = await client.get(media_url, headers=headers, follow_redirects=True)
        resp.raise_for_status()
        return resp.content


whatsapp_client = WhatsAppClient()
