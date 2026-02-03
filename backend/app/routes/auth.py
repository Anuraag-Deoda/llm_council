"""
Authentication routes for LLM Council
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.database import get_db
from app.services.auth_service import auth_service
from app.core.security import TokenPair

router = APIRouter(prefix="/auth", tags=["authentication"])


# ============================================================================
# Request/Response Models
# ============================================================================

class RegisterRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8)
    display_name: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class MagicLinkRequest(BaseModel):
    """Magic link request"""
    email: EmailStr


class RefreshRequest(BaseModel):
    """Token refresh request"""
    refresh_token: str


class UpdateProfileRequest(BaseModel):
    """Profile update request"""
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    preferences: Optional[dict] = None


class SetPasswordRequest(BaseModel):
    """Set password request"""
    password: str = Field(..., min_length=8)


class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    email_verified: bool
    display_name: Optional[str]
    avatar_url: Optional[str]
    preferences: dict
    is_active: bool
    has_password: bool
    created_at: str
    last_login_at: Optional[str]


class AuthResponse(BaseModel):
    """Authentication response with tokens and user"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class MessageResponse(BaseModel):
    """Simple message response"""
    message: str
    success: bool = True


# ============================================================================
# Helper Functions
# ============================================================================

def get_current_user_from_token(
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """Get current user from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header"
        )

    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format"
        )

    token = parts[1]
    user, error = auth_service.get_current_user(db, token)

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    return user


def user_to_response(user) -> UserResponse:
    """Convert user model to response"""
    return UserResponse(
        id=user.id,
        email=user.email,
        email_verified=user.email_verified,
        display_name=user.display_name,
        avatar_url=user.avatar_url,
        preferences=user.preferences or {},
        is_active=user.is_active,
        has_password=user.password_hash is not None,
        created_at=user.created_at.isoformat() if user.created_at else None,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None
    )


def tokens_to_auth_response(tokens: TokenPair, user) -> AuthResponse:
    """Convert token pair and user to auth response"""
    return AuthResponse(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        token_type=tokens.token_type,
        expires_in=tokens.expires_in,
        user=user_to_response(user)
    )


# ============================================================================
# Routes
# ============================================================================

@router.post("/register", response_model=AuthResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user with email and password.

    A verification email will be sent to confirm the email address.
    """
    user, error = auth_service.register_user(
        db,
        email=request.email,
        password=request.password,
        display_name=request.display_name
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Login user immediately after registration
    from app.core.security import create_token_pair
    tokens = create_token_pair(user.id, user.email)

    return tokens_to_auth_response(tokens, user)


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Login with email and password.

    Returns access and refresh tokens.
    """
    tokens, error = auth_service.login(
        db,
        email=request.email,
        password=request.password
    )

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    user = auth_service.get_user_by_email(db, request.email)
    return tokens_to_auth_response(tokens, user)


@router.post("/magic-link", response_model=MessageResponse)
def request_magic_link(request: MagicLinkRequest, db: Session = Depends(get_db)):
    """
    Request a magic link for passwordless authentication.

    A link will be sent to the email address that can be used to sign in.
    """
    success = auth_service.send_magic_link(db, request.email, token_type="login")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send magic link"
        )

    return MessageResponse(
        message="Magic link sent! Check your email.",
        success=True
    )


@router.get("/verify/{token}", response_model=AuthResponse)
def verify_magic_link(token: str, db: Session = Depends(get_db)):
    """
    Verify a magic link token.

    Returns access and refresh tokens if valid.
    Creates a new user if the email is not registered.
    """
    tokens, error = auth_service.verify_magic_link(db, token)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    # Get the user from the token
    from app.core.security import verify_access_token
    token_data = verify_access_token(tokens.access_token)
    user = auth_service.get_user_by_id(db, token_data.user_id)

    return tokens_to_auth_response(tokens, user)


@router.post("/refresh", response_model=AuthResponse)
def refresh_tokens(request: RefreshRequest, db: Session = Depends(get_db)):
    """
    Refresh access token using refresh token.

    Returns new access and refresh tokens.
    """
    tokens, error = auth_service.refresh_tokens(db, request.refresh_token)

    if error:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=error
        )

    # Get user from new tokens
    from app.core.security import verify_access_token
    token_data = verify_access_token(tokens.access_token)
    user = auth_service.get_user_by_id(db, token_data.user_id)

    return tokens_to_auth_response(tokens, user)


@router.get("/me", response_model=UserResponse)
def get_me(user=Depends(get_current_user_from_token)):
    """
    Get current user profile.

    Requires valid access token.
    """
    return user_to_response(user)


@router.put("/me", response_model=UserResponse)
def update_me(
    request: UpdateProfileRequest,
    user=Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Update current user profile.

    Requires valid access token.
    """
    updated_user = auth_service.update_user(
        db,
        user=user,
        display_name=request.display_name,
        avatar_url=request.avatar_url,
        preferences=request.preferences
    )

    return user_to_response(updated_user)


@router.post("/me/password", response_model=MessageResponse)
def set_password(
    request: SetPasswordRequest,
    user=Depends(get_current_user_from_token),
    db: Session = Depends(get_db)
):
    """
    Set or update password for current user.

    Requires valid access token.
    """
    success, error = auth_service.set_password(db, user, request.password)

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return MessageResponse(
        message="Password updated successfully",
        success=True
    )


@router.post("/resend-verification", response_model=MessageResponse)
def resend_verification(user=Depends(get_current_user_from_token), db: Session = Depends(get_db)):
    """
    Resend verification email.

    Requires valid access token.
    """
    if user.email_verified:
        return MessageResponse(
            message="Email already verified",
            success=True
        )

    success = auth_service.send_magic_link(db, user.email, token_type="verify")

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

    return MessageResponse(
        message="Verification email sent!",
        success=True
    )
