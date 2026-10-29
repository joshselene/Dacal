# apps/api/app/routers/auth.py
"""Authentication API routes (FastAPI).
Provides:
* POST /register – create organisation (if new) and tutor, return JWT pair.
* POST /login – validate credentials, return JWT pair.
* POST /refresh – exchange refresh token for a new access token.
* POST /logout – clear refresh‑token cookie.
All responses use the ``TokenResponse`` schema defined in ``app.schemas.auth``.
"""

from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status, Cookie
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..schemas.auth import RegisterRequest, LoginRequest, TokenResponse
from ..services.auth_service import (
    register_tutor,
    authenticate_tutor,
    build_login_response,
)
from ..models.tutor import Tutor

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
def register(
    request: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        tutor = register_tutor(
            db=db,
            email=request.email,
            raw_password=request.password,
            full_name=request.full_name,
            organisation_name=request.organisation_name,
        )
        db.commit()
    except ValueError as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc))

    token_payload = build_login_response(tutor)
    # Set refresh token as httpOnly cookie
    response.set_cookie(
        key="refresh_token",
        value=token_payload["refresh_token"],
        httponly=True,
        secure=False,  # set True in prod (HTTPS)
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return TokenResponse(**token_payload)


@router.post("/login", response_model=TokenResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        tutor = authenticate_tutor(db, request.email, request.password)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))

    token_payload = build_login_response(tutor)
    response.set_cookie(
        key="refresh_token",
        value=token_payload["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return TokenResponse(**token_payload)


@router.post("/refresh", response_model=TokenResponse)
def refresh(
    refresh_token: str = Cookie(None),
    db: Session = Depends(get_db),
    response: Response = None,
):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token missing")
    from ..utils.security import decode_token

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    tutor_id = payload.get("sub")
    if not tutor_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")
    tutor = db.query(Tutor).filter(Tutor.id == tutor_id).first()
    if not tutor:
        raise HTTPException(status_code=401, detail="Tutor not found")
    token_payload = build_login_response(tutor)
    # Reset refresh cookie
    if response is None:
        response = Response()
    response.set_cookie(
        key="refresh_token",
        value=token_payload["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=7 * 24 * 60 * 60,
    )
    return TokenResponse(**token_payload)


@router.post("/logout")
def logout(response: Response):
    # Delete the httpOnly refresh cookie
    response.delete_cookie(key="refresh_token")
    return {"detail": "Logged out"}
