import os
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from psycopg import Connection

from app.database import Database, get_connection, serialize_row

SECRET_KEY = os.getenv("JWT_SECRET_KEY", "buildsync-dev-secret-change-me-2026-qa-strong")
ALGORITHM = "HS256"
security = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_access_token(username: str, role: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=8)
    payload = {"sub": username, "role": role, "exp": exp}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as exc:  # pragma: no cover - defensive branch for invalid tokens
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Connection[dict[str, Any]] = Depends(get_connection),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_access_token(credentials.credentials)
    username = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token missing user information",
            headers={"WWW-Authenticate": "Bearer"},
        )

    row = db.execute(
        "SELECT * FROM app_users WHERE username = %s AND is_active = TRUE",
        [username],
    ).fetchone()
    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return serialize_row(row)


def require_roles(*allowed_roles: str):
    def dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user.get("role") not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires one of these roles: {', '.join(allowed_roles)}",
            )
        return current_user

    return dependency


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class UserIdentity(BaseModel):
    user_id: str
    username: str
    role: str
    employee_id: str | None = None


class AuthLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserIdentity


auth_router = APIRouter(tags=["Authentication"])


@auth_router.post("/auth/login", response_model=AuthLoginResponse, summary="Authenticate a user and issue a JWT")
def login(data: LoginRequest, db: Database) -> dict[str, Any]:
    row = db.execute(
        "SELECT * FROM app_users WHERE username = %s AND is_active = TRUE",
        [data.username],
    ).fetchone()
    if row is None or not verify_password(data.password, row["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(row["username"], row["role"])
    user = serialize_row(row)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"],
            "employee_id": user.get("employee_id"),
        },
    }


@auth_router.get("/auth/me", summary="Return the current authenticated user")
def current_user_profile(current_user: dict[str, Any] = Depends(require_roles("admin", "employee"))) -> dict[str, Any]:
    return {
        "user_id": current_user["user_id"],
        "username": current_user["username"],
        "role": current_user["role"],
        "employee_id": current_user.get("employee_id"),
    }
