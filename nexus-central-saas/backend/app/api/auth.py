"""Engineer Authentication API Endpoints"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.core.security import verify_password, create_access_token, decode_access_token
from app.models.entities import User

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    username: str
    role: str


def get_current_engineer(authorization: Optional[str] = Header(None)) -> str:
    """Dependency ensuring caller is an authenticated engineer."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Authorization header",
        )
    token = authorization.split(" ")[1]
    payload = decode_access_token(token)
    if not payload or not payload.get("sub"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired engineer session token",
        )
    return payload["sub"]


@auth_router.post("/login", response_model=LoginResponse)
def login(creds: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate an engineer and return JWT session token."""
    # Check default engineer account from settings or DB
    if creds.username == settings.ENGINEER_USERNAME:
        if not verify_password(creds.password, settings.ENGINEER_PASSWORD_HASH):
            raise HTTPException(status_code=401, detail="Invalid username or password")
        token = create_access_token(subject=creds.username, data={"role": "engineer"})
        return LoginResponse(access_token=token, username=creds.username, role="engineer")

    # Check database users
    user = db.query(User).filter(User.username == creds.username).first()
    if not user or not verify_password(creds.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(subject=user.username, data={"role": user.role})
    return LoginResponse(access_token=token, username=user.username, role=user.role)
