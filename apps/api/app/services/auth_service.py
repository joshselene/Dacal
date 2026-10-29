# apps/api/app/services/auth_service.py
"""Authentication service – encapsulates user & organisation creation, password handling,
JWT generation and refresh‑token logic.
All functions are pure Python (no FastAPI dependencies) so they can be unit‑tested
in isolation.
"""

import uuid
from datetime import datetime, timedelta
from typing import Mapping, Any

from sqlalchemy.orm import Session

from ..models.tutor import Tutor
from ..models.organisation import Organisation
from ..utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
)


def get_or_create_organisation(db: Session, name: str) -> Organisation:
    """Return an existing organisation with *name* or create a new one.
    The name column is unique, so we first query; if not found we insert.
    """
    org = (
        db.query(Organisation)
        .filter(Organisation.name == name, Organisation.is_active == True)
        .first()
    )
    if org:
        return org
    org = Organisation(name=name)
    db.add(org)
    db.flush()  # assign primary key
    return org


def register_tutor(
    db: Session,
    email: str,
    raw_password: str,
    full_name: str | None,
    organisation_name: str,
) -> Tutor:
    """Create a new tutor and (if needed) a new organisation.
    Raises ``ValueError`` if the e‑mail already exists.
    """
    if db.query(Tutor).filter(Tutor.email == email).first():
        raise ValueError("Email already registered")
    org = get_or_create_organisation(db, organisation_name)
    pwd_hash = hash_password(raw_password)
    tutor = Tutor(
        email=email,
        password_hash=pwd_hash,
        full_name=full_name,
        organisation_id=org.id,
    )
    db.add(tutor)
    db.flush()
    return tutor


def authenticate_tutor(db: Session, email: str, raw_password: str) -> Tutor:
    """Validate credentials and return the Tutor record.
    Raises ``ValueError`` on failure.
    """
    tutor = (
        db.query(Tutor)
        .filter(Tutor.email == email, Tutor.is_active == True)
        .first()
    )
    if not tutor:
        raise ValueError("Invalid credentials")
    if not verify_password(raw_password, tutor.password_hash):
        raise ValueError("Invalid credentials")
    return tutor



def build_login_response(tutor: Tutor) -> Mapping[str, Any]:
    """Create JWT access and refresh payloads for the tutor."""
    data = {
        "sub": str(tutor.id),
        "org_id": str(tutor.organisation_id),
    }

    access = create_access_token(data)
    refresh = create_refresh_token(data)

    return {
        "access_token": access["token"],
        "expires_at": access["expires_at"],
        "refresh_token": refresh["token"],
        "refresh_expires_at": refresh["expires_at"],
        "token_type": "bearer",
    }

