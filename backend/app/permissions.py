from typing import Any

from fastapi import Depends, HTTPException, status

from app.auth import get_current_user


def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user


def require_employee_or_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if current_user.get("role") not in {"employee", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Employee or admin privileges required",
        )
    return current_user
