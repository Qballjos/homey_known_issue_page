from typing import Optional
from fastapi import Request, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.config import settings
from app.auth.security import verify_session_token


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Extract user from either session cookie or Authorization Bearer header."""
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    
    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

    if not token:
        return None

    data = verify_session_token(token)
    if not data or "user_id" not in data:
        return None

    user = db.query(User).filter(User.id == data["user_id"], User.is_active == True).first()
    return user


def require_admin_api(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Dependency for REST API endpoints requiring Admin authentication."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Administrator access required",
        )
    return user


def require_admin_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    """Dependency for web UI admin routes; redirects to login if unauthenticated."""
    if not user or user.role != "admin":
        # Raise HTTP 303 Redirect to login page
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": f"/admin/login?next={request.url.path}"}
        )
    return user
