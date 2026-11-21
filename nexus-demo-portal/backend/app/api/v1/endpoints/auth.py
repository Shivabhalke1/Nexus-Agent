"""Authentication API endpoints and user security context."""
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_access_token
from app.core.exceptions import UnauthorizedException, NotFoundException
from app.models.user import User
from app.schemas.response import APIResponse
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse
from app.services.auth_service import register_user, authenticate_user, emit_auth_event

router = APIRouter(prefix="/auth", tags=["Authentication & User Management"])
security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Dependency verifying JWT token and returning authenticated User entity."""
    if not credentials:
        raise UnauthorizedException("Authentication token missing")

    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise UnauthorizedException("Invalid or expired authentication token")

    user_id = payload["sub"]
    try:
        user_id_int = int(user_id)
    except (ValueError, TypeError):
        raise UnauthorizedException("Invalid user token payload")

    user = db.query(User).filter(User.id == user_id_int, User.is_active == True).first()
    if not user:
        raise UnauthorizedException("User no longer exists or is inactive")

    return user


@router.post("/register", response_model=APIResponse[TokenResponse], status_code=status.HTTP_201_CREATED)
def register(
    user_in: UserRegister,
    request: Request,
    db: Session = Depends(get_db),
):
    """Register a new customer account and return an access token."""
    request_id = getattr(request.state, "request_id", None)
    result = register_user(db=db, user_in=user_in, request_id=request_id)
    return APIResponse(
        success=True,
        message="User account created successfully",
        data=result,
    )


@router.post("/login", response_model=APIResponse[TokenResponse])
def login(
    login_in: UserLogin,
    request: Request,
    db: Session = Depends(get_db),
):
    """Authenticate with email and password, issuing a signed JWT access token."""
    request_id = getattr(request.state, "request_id", None)
    result = authenticate_user(db=db, login_in=login_in, request_id=request_id)
    return APIResponse(
        success=True,
        message="Login successful",
        data=result,
    )


@router.post("/logout", response_model=APIResponse[None])
def logout(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Record user logout event."""
    request_id = getattr(request.state, "request_id", None)
    emit_auth_event(
        db=db,
        event_type="AUTH_LOGOUT",
        user_id=current_user.id,
        email=current_user.email,
        request_id=request_id,
        severity="INFO",
    )
    return APIResponse(
        success=True,
        message="Logged out successfully",
        data=None,
    )


@router.get("/me", response_model=APIResponse[UserResponse])
def get_current_user_profile(
    current_user: User = Depends(get_current_user),
):
    """Retrieve authenticated user's profile."""
    return APIResponse(
        success=True,
        message="User profile retrieved successfully",
        data=UserResponse.model_validate(current_user),
    )
