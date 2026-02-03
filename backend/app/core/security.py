"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional, Any
import secrets
import uuid

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import settings


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """JWT token payload data"""
    user_id: str
    email: str
    token_type: str = "access"
    exp: Optional[datetime] = None


class TokenPair(BaseModel):
    """Access and refresh token pair"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT access token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.jwt_access_token_expire_minutes)

    to_encode = {
        "sub": user_id,
        "email": email,
        "type": "access",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_refresh_token(
    user_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Create a JWT refresh token"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_token_expire_days)

    to_encode = {
        "sub": user_id,
        "email": email,
        "type": "refresh",
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def create_token_pair(user_id: str, email: str) -> TokenPair:
    """Create both access and refresh tokens"""
    access_token = create_access_token(user_id, email)
    refresh_token = create_refresh_token(user_id, email)

    return TokenPair(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.jwt_access_token_expire_minutes * 60
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None


def verify_access_token(token: str) -> Optional[TokenData]:
    """Verify an access token and return the token data"""
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != "access":
        return None

    user_id = payload.get("sub")
    email = payload.get("email")

    if user_id is None or email is None:
        return None

    return TokenData(
        user_id=user_id,
        email=email,
        token_type="access"
    )


def verify_refresh_token(token: str) -> Optional[TokenData]:
    """Verify a refresh token and return the token data"""
    payload = decode_token(token)
    if payload is None:
        return None

    if payload.get("type") != "refresh":
        return None

    user_id = payload.get("sub")
    email = payload.get("email")

    if user_id is None or email is None:
        return None

    return TokenData(
        user_id=user_id,
        email=email,
        token_type="refresh"
    )


def generate_magic_link_token() -> str:
    """Generate a secure random token for magic links"""
    return secrets.token_urlsafe(32)


def generate_user_id() -> str:
    """Generate a unique user ID"""
    return str(uuid.uuid4())
