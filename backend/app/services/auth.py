from __future__ import annotations

import hashlib
import hmac
import secrets
import uuid
from datetime import UTC, datetime, timedelta

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(owner_id: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.jwt_access_token_expire_minutes
    )
    payload = {"sub": owner_id, "exp": expires_at}
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def decode_access_token(token: str) -> str:
    """Return the owner_id from a valid JWT, or raise."""
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
    owner_id: str = payload["sub"]
    return owner_id


def generate_id() -> str:
    return uuid.uuid4().hex[:16]


def generate_email_verification_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def hash_email_verification_code(code: str) -> str:
    settings = get_settings()
    peppered = f"{settings.jwt_secret_key}:{code}".encode()
    return hashlib.sha256(peppered).hexdigest()


def verify_email_verification_code(code: str, code_hash: str) -> bool:
    expected = hash_email_verification_code(code)
    return hmac.compare_digest(expected, code_hash)


def compute_email_verification_expiry() -> datetime:
    settings = get_settings()
    return datetime.now(UTC) + timedelta(minutes=settings.email_verification_ttl_minutes)
