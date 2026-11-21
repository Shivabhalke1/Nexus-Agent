"""Security, hashing, and payload integrity verification."""
import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
from jose import jwt, JWTError
from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash plaintext admin password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def create_access_token(
    subject: Optional[str] = None,
    data: Optional[Dict[str, Any]] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create signed administrator JWT session token."""
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    sub = subject or (data.get("sub") if data else "admin")
    to_encode = {"sub": sub, "exp": expire, "iat": datetime.now(timezone.utc), "role": "admin"}
    if data:
        to_encode.update(data)
        to_encode["exp"] = expire
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    """Validate and decode administrator JWT session token."""
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def compute_payload_integrity_hash(payload: Dict[str, Any]) -> str:
    """Compute SHA-256 canonical hash of payload to guarantee tamper resistance."""
    canonical_json = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
