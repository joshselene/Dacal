# apps/api/app/schemas/auth.py
"""Pydantic v2 schemas for authentication endpoints.
These are used by FastAPI request bodies and responses.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

class TokenPayload(BaseModel):
    sub: UUID  # tutor ID
    org_id: UUID  # organisation ID

class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    expires_at: datetime = Field(..., description="UTC expiry timestamp")
    refresh_token: str = Field(..., description="JWT refresh token")
    refresh_expires_at: datetime = Field(..., description="UTC expiry for refresh token")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    organisation_name: str = Field(..., description="Name of the school/tenant to create or join")

    @validator("password")
    def disallow_common(cls, v: str) -> str:
        common = {"password", "12345678", "qwerty", "letmein"}
        if v.lower() in common:
            raise ValueError("Password is too common")
        return v
