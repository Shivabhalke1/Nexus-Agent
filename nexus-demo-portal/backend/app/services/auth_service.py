"""Authentication service managing accounts, sessions, and telemetry events."""
import json
import logging
from typing import Optional
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.security import hash_password, verify_password, create_access_token
from app.core.exceptions import ConflictException, UnauthorizedException
from app.models.user import User
from app.models.event import ApplicationEvent
from app.schemas.user import UserRegister, UserLogin, TokenResponse, UserResponse

logger = logging.getLogger(settings.SERVICE_NAME)


def emit_auth_event(
    db: Session,
    event_type: str,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
    request_id: Optional[str] = None,
    severity: str = "INFO",
    error_message: Optional[str] = None,
) -> None:
    """Emit an authentication telemetry event without leaking passwords or secrets."""
    try:
        payload_data = {
            "event": event_type,
            "user_id": user_id,
            "email_domain": email.split("@")[-1] if email and "@" in email else None,
            "service": settings.SERVICE_NAME,
        }
        if error_message:
            payload_data["error"] = error_message

        event = ApplicationEvent(
            event_type=event_type,
            request_id=request_id,
            severity=severity,
            payload=json.dumps(payload_data),
        )
        db.add(event)
        db.commit()

        # Structured application logging
        log_msg = f"Auth event: type={event_type} user_id={user_id} request_id={request_id}"
        if severity == "WARNING":
            logger.warning(log_msg)
        else:
            logger.info(log_msg)
    except Exception as exc:
        logger.error(f"Failed to record auth event: {str(exc)}")


def register_user(db: Session, user_in: UserRegister, request_id: Optional[str] = None) -> TokenResponse:
    """Register a new user account with hashed password and initial token."""
    existing_user = db.query(User).filter(User.email == user_in.email.lower()).first()
    if existing_user:
        emit_auth_event(
            db,
            event_type="AUTH_REGISTER_CONFLICT",
            email=user_in.email,
            request_id=request_id,
            severity="WARNING",
            error_message="Email already registered",
        )
        raise ConflictException(f"User with email '{user_in.email}' already exists.")

    new_user = User(
        email=user_in.email.lower(),
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name,
        role="customer",
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    emit_auth_event(
        db,
        event_type="USER_REGISTERED",
        user_id=new_user.id,
        email=new_user.email,
        request_id=request_id,
        severity="INFO",
    )

    token = create_access_token(subject=new_user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(new_user),
    )


def authenticate_user(db: Session, login_in: UserLogin, request_id: Optional[str] = None) -> TokenResponse:
    """Validate user credentials and issue signed access token."""
    user = db.query(User).filter(User.email == login_in.email.lower()).first()
    
    if not user or not verify_password(login_in.password, user.hashed_password):
        emit_auth_event(
            db,
            event_type="AUTH_LOGIN_FAILED",
            email=login_in.email,
            request_id=request_id,
            severity="WARNING",
            error_message="Invalid credentials",
        )
        raise UnauthorizedException("Invalid email or password.")

    if not user.is_active:
        emit_auth_event(
            db,
            event_type="AUTH_LOGIN_INACTIVE_USER",
            user_id=user.id,
            request_id=request_id,
            severity="WARNING",
            error_message="Account disabled",
        )
        raise UnauthorizedException("User account is inactive.")

    emit_auth_event(
        db,
        event_type="AUTH_LOGIN_SUCCESS",
        user_id=user.id,
        email=user.email,
        request_id=request_id,
        severity="INFO",
    )

    token = create_access_token(subject=user.id)
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )
