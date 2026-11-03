"""Utility functions for password hashing and JWT handling.

The project uses Argon2 for password hashing (argon2‑cffi) and
python‑jose for JSON Web Tokens. Secrets and expiry settings are taken
from environment variables so that no production secrets are hard‑coded.
"""

import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from argon2 import PasswordHasher
from jose import JWTError, jwt

# ---------------------------------------------------------------------------
# Password handling
# ---------------------------------------------------------------------------

_password_hasher = PasswordHasher()


def hash_password(password: str) -> str:
    """Return Argon2 hash of *password*.

    The Argon2 hasher includes a random salt and suitable work factor.
    """
    return _password_hasher.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Return ``True`` if *password* matches the stored *hashed* value.

    ``argon2‑cffi`` raises an exception on mismatch; we translate that to a
    simple boolean for the caller.
    """
    try:
        return _password_hasher.verify(hashed, password)
    except Exception:
        return False

# ---------------------------------------------------------------------------
# JWT handling
# ---------------------------------------------------------------------------

_JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "change-me-in-prod")
_JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
_ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
_REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))


def _create_token(data: Dict[str, Any], expires_delta: timedelta, token_type: str) -> Dict[str, Any]:
    """Create a JWT with *data* payload and expiry.

    Returns a dict containing the token string and the absolute expiry
    datetime (ISO‑8601) for convenience.
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire, "type": token_type})
    encoded_jwt = jwt.encode(to_encode, _JWT_SECRET_KEY, algorithm=_JWT_ALGORITHM)
    return {"token": encoded_jwt, "expires_at": expire.isoformat()}


def create_access_token(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create an access token (short‑lived)."""
    return _create_token(
        data,
        timedelta(minutes=_ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
    )


def create_refresh_token(data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a refresh token (long‑lived)."""
    return _create_token(
        data,
        timedelta(days=_REFRESH_TOKEN_EXPIRE_DAYS),
        token_type="refresh",
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Validate *token* and return its payload or ``None`` on failure."""
    try:
        payload = jwt.decode(token, _JWT_SECRET_KEY, algorithms=[_JWT_ALGORITHM])
        return payload
    except JWTError:
        return None
