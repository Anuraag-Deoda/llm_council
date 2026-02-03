"""
Authentication service for user management and authentication
"""
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from app.config import settings
from app.core.security import (
    verify_password,
    get_password_hash,
    create_token_pair,
    verify_access_token,
    verify_refresh_token,
    generate_magic_link_token,
    generate_user_id,
    TokenPair,
    TokenData
)
from app.database.auth_models import User, MagicLinkToken
from app.services.email_service import email_service

logger = logging.getLogger(__name__)


class AuthService:
    """Service for handling authentication operations"""

    def get_user_by_id(self, db: Session, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        return db.query(User).filter(User.id == user_id).first()

    def get_user_by_email(self, db: Session, email: str) -> Optional[User]:
        """Get a user by email"""
        return db.query(User).filter(User.email == email.lower()).first()

    def create_user(
        self,
        db: Session,
        email: str,
        password: Optional[str] = None,
        display_name: Optional[str] = None,
        email_verified: bool = False
    ) -> User:
        """Create a new user"""
        user = User(
            id=generate_user_id(),
            email=email.lower(),
            password_hash=get_password_hash(password) if password else None,
            display_name=display_name,
            email_verified=email_verified,
            preferences={},
            is_active=True
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Send welcome email for verified users
        if email_verified:
            email_service.send_welcome_email(email, display_name)

        logger.info(f"Created new user: {user.id} ({email})")
        return user

    def register_user(
        self,
        db: Session,
        email: str,
        password: str,
        display_name: Optional[str] = None
    ) -> Tuple[Optional[User], Optional[str]]:
        """Register a new user with email and password"""
        # Check if user already exists
        existing_user = self.get_user_by_email(db, email)
        if existing_user:
            return None, "Email already registered"

        # Validate password
        if len(password) < 8:
            return None, "Password must be at least 8 characters"

        # Create user
        user = self.create_user(
            db,
            email=email,
            password=password,
            display_name=display_name,
            email_verified=False
        )

        # Send verification email
        self.send_magic_link(db, email, token_type="verify")

        return user, None

    def authenticate_user(
        self,
        db: Session,
        email: str,
        password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate a user with email and password"""
        user = self.get_user_by_email(db, email)

        if not user:
            return None, "Invalid email or password"

        if not user.is_active:
            return None, "Account is disabled"

        if not user.password_hash:
            return None, "Please use magic link to sign in"

        if not verify_password(password, user.password_hash):
            return None, "Invalid email or password"

        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()

        return user, None

    def login(
        self,
        db: Session,
        email: str,
        password: str
    ) -> Tuple[Optional[TokenPair], Optional[str]]:
        """Login and return tokens"""
        user, error = self.authenticate_user(db, email, password)
        if error:
            return None, error

        tokens = create_token_pair(user.id, user.email)
        return tokens, None

    def send_magic_link(
        self,
        db: Session,
        email: str,
        token_type: str = "login"
    ) -> bool:
        """Send a magic link email"""
        # Generate token
        token = generate_magic_link_token()

        # Calculate expiration
        expires_at = datetime.utcnow() + timedelta(minutes=settings.magic_link_expire_minutes)

        # Invalidate any existing tokens for this email and type
        db.query(MagicLinkToken).filter(
            MagicLinkToken.email == email.lower(),
            MagicLinkToken.token_type == token_type,
            MagicLinkToken.used_at.is_(None)
        ).update({"used_at": datetime.utcnow()})

        # Create new token
        magic_token = MagicLinkToken(
            token=token,
            email=email.lower(),
            token_type=token_type,
            expires_at=expires_at
        )
        db.add(magic_token)
        db.commit()

        # Send email
        is_login = token_type == "login"
        success = email_service.send_magic_link(email, token, is_login)

        if success:
            logger.info(f"Magic link sent to {email} (type: {token_type})")

        return success

    def verify_magic_link(
        self,
        db: Session,
        token: str
    ) -> Tuple[Optional[TokenPair], Optional[str]]:
        """Verify a magic link token and return auth tokens"""
        # Find token
        magic_token = db.query(MagicLinkToken).filter(
            MagicLinkToken.token == token,
            MagicLinkToken.used_at.is_(None)
        ).first()

        if not magic_token:
            return None, "Invalid or expired link"

        # Check expiration
        if magic_token.expires_at < datetime.utcnow():
            return None, "Link has expired"

        # Mark token as used
        magic_token.used_at = datetime.utcnow()

        # Get or create user
        user = self.get_user_by_email(db, magic_token.email)

        if not user:
            # Create new user for login magic links
            user = self.create_user(
                db,
                email=magic_token.email,
                email_verified=True
            )
        else:
            # Mark email as verified if this is a verify token
            if magic_token.token_type == "verify":
                user.email_verified = True

            # Update last login
            user.last_login_at = datetime.utcnow()

        db.commit()

        # Generate tokens
        tokens = create_token_pair(user.id, user.email)

        logger.info(f"Magic link verified for {user.email}")
        return tokens, None

    def refresh_tokens(
        self,
        db: Session,
        refresh_token: str
    ) -> Tuple[Optional[TokenPair], Optional[str]]:
        """Refresh access token using refresh token"""
        token_data = verify_refresh_token(refresh_token)

        if not token_data:
            return None, "Invalid refresh token"

        # Verify user still exists and is active
        user = self.get_user_by_id(db, token_data.user_id)

        if not user:
            return None, "User not found"

        if not user.is_active:
            return None, "Account is disabled"

        # Generate new tokens
        tokens = create_token_pair(user.id, user.email)

        return tokens, None

    def get_current_user(
        self,
        db: Session,
        token: str
    ) -> Tuple[Optional[User], Optional[str]]:
        """Get current user from access token"""
        token_data = verify_access_token(token)

        if not token_data:
            return None, "Invalid token"

        user = self.get_user_by_id(db, token_data.user_id)

        if not user:
            return None, "User not found"

        if not user.is_active:
            return None, "Account is disabled"

        return user, None

    def update_user(
        self,
        db: Session,
        user: User,
        display_name: Optional[str] = None,
        avatar_url: Optional[str] = None,
        preferences: Optional[dict] = None
    ) -> User:
        """Update user profile"""
        if display_name is not None:
            user.display_name = display_name

        if avatar_url is not None:
            user.avatar_url = avatar_url

        if preferences is not None:
            user.preferences = {**user.preferences, **preferences}

        db.commit()
        db.refresh(user)

        return user

    def set_password(
        self,
        db: Session,
        user: User,
        new_password: str
    ) -> Tuple[bool, Optional[str]]:
        """Set or update user password"""
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters"

        user.password_hash = get_password_hash(new_password)
        db.commit()

        return True, None

    def cleanup_expired_tokens(self, db: Session) -> int:
        """Clean up expired magic link tokens"""
        result = db.query(MagicLinkToken).filter(
            MagicLinkToken.expires_at < datetime.utcnow()
        ).delete()
        db.commit()

        if result > 0:
            logger.info(f"Cleaned up {result} expired magic link tokens")

        return result


# Singleton instance
auth_service = AuthService()
