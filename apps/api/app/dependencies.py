# apps/api/app/dependencies.py
"""FastAPI dependency helpers.
* ``get_db`` – yields a SQLAlchemy session (imported from ``app.db``).
* ``get_current_tutor`` – extracts the JWT from the ``Authorization`` header,
  validates it, and returns the ``Tutor`` ORM instance.
"""

import uuid
from typing import Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from .db import get_db
from .models.tutor import Tutor
from .utils.security import decode_token

security = HTTPBearer(auto_error=False)


def get_current_tutor(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Tutor:
    """Validate JWT and return the logged-in Tutor.
    Raises ``401 Unauthorized`` if the token is missing, invalid, or the tutor
    cannot be found.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication credentials",
        )
    token = credentials.credentials
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )
    raw_sub = payload.get("sub")
    if raw_sub is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token payload missing 'sub' claim",
        )
    try:
        tutor_id = raw_sub if isinstance(raw_sub, uuid.UUID) else uuid.UUID(str(raw_sub))
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid subject identifier in token",
        )
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id, Tutor.is_active == True).first()
    if tutor is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tutor not found or inactive",
        )
    return tutor


def require_roles(*allowed_roles: str) -> Callable[[Tutor], Tutor]:
    """Role-based access control guard (FR-01). Returns 403 for disallowed roles."""

    def _check_role(tutor: Tutor = Depends(get_current_tutor)) -> Tutor:
        if allowed_roles and tutor.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{tutor.role}' is not permitted to perform this action.",
            )
        return tutor

    return _check_role
