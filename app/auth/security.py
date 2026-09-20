import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import Optional, Dict, Any
import bcrypt
from app.config import settings


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def generate_secure_token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def create_session_token(data: Dict[str, Any], max_age_seconds: int = 86400 * 7) -> str:
    """Create a tamper-proof signed session token."""
    payload = {
        "exp": int(time.time()) + max_age_seconds,
        "data": data,
        "nonce": secrets.token_hex(8)
    }
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    b64_payload = base64.urlsafe_b64encode(raw).decode("utf-8").rstrip("=")
    
    signature = hmac.new(
        settings.SECRET_KEY.encode("utf-8"),
        b64_payload.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()
    
    return f"{b64_payload}.{signature}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode a signed session token."""
    if not token or "." not in token:
        return None
    try:
        b64_payload, signature = token.rsplit(".", 1)
        expected_sig = hmac.new(
            settings.SECRET_KEY.encode("utf-8"),
            b64_payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return None

        # Fix base64 padding
        padding = 4 - (len(b64_payload) % 4)
        if padding != 4:
            b64_payload += "=" * padding

        raw = base64.urlsafe_b64decode(b64_payload.encode("utf-8"))
        payload = json.loads(raw.decode("utf-8"))

        if payload.get("exp", 0) < time.time():
            return None

        return payload.get("data")
    except Exception:
        return None
