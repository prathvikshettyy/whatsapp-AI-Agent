"""WhatsApp Cloud API client service."""

import re
from typing import Any, Dict, List, Optional, Tuple
import httpx
import structlog

from backend.app.config import settings

logger = structlog.get_logger(__name__)


def mask_phone_number(phone: str) -> str:
    """Mask phone number in logs to protect PII."""
    if not phone:
        return "unknown"
    cleaned = re.sub(r"[^\d+]", "", phone)
    if len(cleaned) <= 6:
        return "****"
    return f"{cleaned[:3]} ••••• {cleaned[-4:]}"


def split_message(text: str, max_length: int = 4096) -> List[str]:
    """Split message into chunks avoiding breaking sentences or words."""
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

        split_idx = -1
        # Try paragraph
        para_idx = remaining.rfind("\n\n", 0, max_length)
        if para_idx != -1 and para_idx >= max_length // 3:
            split_idx = para_idx + 2
        else:
            # Try single line
            line_idx = remaining.rfind("\n", 0, max_length)
            if line_idx != -1 and line_idx >= max_length // 3:
                split_idx = line_idx + 1
            else:
                # Try sentence
                period_idx = max(
                    remaining.rfind(". ", 0, max_length),
                    remaining.rfind("! ", 0, max_length),
                    remaining.rfind("? ", 0, max_length),
                )
                if period_idx != -1 and period_idx >= max_length // 3:
                    split_idx = period_idx + 2
                else:
                    # Space
                    space_idx = remaining.rfind(" ", 0, max_length)
                    split_idx = space_idx + 1 if space_idx != -1 else max_length

        chunk = remaining[:split_idx].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_idx:].strip()

    return chunks


class WhatsAppService:
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
        self._client = http_client

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client is not None and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    @property
    def messages_endpoint(self) -> str:
        return f"{self.base_url}/{self.version}/{self.phone_number_id}/messages"

    @property
    def headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    async def send_text(self, to: str, body: str, reply_to_message_id: Optional[str] = None) -> List[Dict[str, Any]]:
        client = await self._get_client()
        chunks = split_message(body, 4096)
        responses = []

        logger.info("sending_whatsapp_text", to=mask_phone_number(to), chunks=len(chunks))

        for idx, chunk in enumerate(chunks):
            payload: Dict[str, Any] = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": to,
                "type": "text",
                "text": {"preview_url": False, "body": chunk},
            }
            if reply_to_message_id and idx == 0:
                payload["context"] = {"message_id": reply_to_message_id}

            try:
                resp = await client.post(self.messages_endpoint, headers=self.headers, json=payload)
                resp.raise_for_status()
                responses.append(resp.json())
            except Exception as e:
                logger.error("whatsapp_send_failed", error=str(e), recipient=mask_phone_number(to))
                raise

        return responses

    async def mark_read(self, message_id: str) -> None:
        client = await self._get_client()
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
        }
        try:
            await client.post(self.messages_endpoint, headers=self.headers, json=payload)
        except Exception as e:
            logger.warning("whatsapp_mark_read_failed", message_id=message_id, error=str(e))

    async def send_template(self, to: str, name: str, lang: str = "en_US", params: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """Send pre-approved template message when outside the 24h window."""
        client = await self._get_client()
        template_obj: Dict[str, Any] = {
            "name": name,
            "language": {"code": lang},
        }
        if params:
            template_obj["components"] = [{"type": "body", "parameters": params}]

        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": template_obj,
        }

        resp = await client.post(self.messages_endpoint, headers=self.headers, json=payload)
        resp.raise_for_status()
        return resp.json()

    async def get_media(self, media_id: str) -> Tuple[bytes, str]:
        """Retrieve media download URL and download media bytes."""
        client = await self._get_client()
        meta_url = f"{self.base_url}/{self.version}/{media_id}"
        resp = await client.get(meta_url, headers=self.headers)
        resp.raise_for_status()
        data = resp.json()
        download_url = data.get("url")
        mime_type = data.get("mime_type", "application/octet-stream")

        # Download raw bytes
        media_resp = await client.get(download_url, headers=self.headers, follow_redirects=True)
        media_resp.raise_for_status()
        return media_resp.content, mime_type


whatsapp_service = WhatsAppService()
