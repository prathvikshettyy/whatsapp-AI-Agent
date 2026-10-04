"""Meta WhatsApp X-Hub-Signature-256 HMAC verification."""

import hashlib
import hmac
from typing import Optional


def verify_meta_signature(app_secret: str, raw_body: bytes, signature_header: Optional[str]) -> bool:
    """
    Validate X-Hub-Signature-256 sent by Meta.
    Format: sha256=<hex_digest>
    """
    if not app_secret:
        return True

    if not signature_header or not signature_header.startswith("sha256="):
        return False

    received_sig = signature_header.split("sha256=", 1)[1]
    expected_sig = hmac.new(
        key=app_secret.encode("utf-8"),
        msg=raw_body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected_sig, received_sig)
