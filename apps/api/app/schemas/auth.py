# apps/api/app/schemas/auth.py
"""Pydantic v2 schemas for authentication endpoints.
These are used by FastAPI request bodies and responses.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


class TokenPayload(BaseModel):
    sub: UUID  # tutor ID
    org_id: UUID  # organisation ID
    role: str = "tutor"


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer")
    expires_at: datetime = Field(..., description="UTC expiry timestamp")
    refresh_token: str = Field(..., description="JWT refresh token")
    refresh_expires_at: datetime = Field(..., description="UTC expiry for refresh token")
    role: str = Field(default="tutor")
    full_name: str | None = None
    email: str | None = None
    organisation_name: str | None = None
    greeting: str = Field(default="Good morning")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    local_hour: int | None = Field(default=None, ge=0, le=23)


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    full_name: str | None = None
    organisation_name: str = Field(..., description="Name of the school/tenant to create or join")
    role: str = Field(default="tutor", description="Role: tutor, admin, support, or learner")
    local_hour: int | None = Field(default=None, ge=0, le=23)

    @field_validator("password")
    @classmethod
    def disallow_common(cls, v: str) -> str:
        common = {"password", "12345678", "qwerty", "letmein"}
        if v.lower() in common:
            raise ValueError("Password is too common")
        return v

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        allowed = {"tutor", "admin", "support", "learner"}
        if v not in allowed:
            raise ValueError(f"Role must be one of {sorted(allowed)}")
        return v
