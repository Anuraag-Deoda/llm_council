"""
Authentication database models for LLM Council
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean,
    JSON, ForeignKey, Index
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .models import Base


class User(Base):
    """User accounts for authentication"""
    __tablename__ = "users"

    id = Column(String(100), primary_key=True)  # UUID
    email = Column(String(255), unique=True, nullable=False, index=True)
    email_verified = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=True)  # Null for magic-link only users
    display_name = Column(String(255), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    preferences = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    last_login_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Model context - information models can use to personalize responses
    model_context = Column(JSON, default=dict)  # {preferred_name, role, expertise, etc.}

    # Relationships - Note: back_populates defined in Conversation model
    conversations = relationship("Conversation", back_populates="user")

    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
    )

    def get_model_context_prompt(self) -> str:
        """Generate a prompt snippet with user context for models."""
        context_parts = []

        if self.display_name:
            context_parts.append(f"The user's name is {self.display_name}.")

        mc = self.model_context or {}

        if mc.get("preferred_name"):
            context_parts.append(f"Address them as {mc['preferred_name']}.")

        if mc.get("role"):
            context_parts.append(f"They work as a {mc['role']}.")

        if mc.get("expertise"):
            expertise = mc["expertise"]
            if isinstance(expertise, list):
                expertise = ", ".join(expertise)
            context_parts.append(f"They have expertise in: {expertise}.")

        if mc.get("communication_style"):
            context_parts.append(f"Preferred communication style: {mc['communication_style']}.")

        if mc.get("technical_level"):
            context_parts.append(f"Technical proficiency: {mc['technical_level']}.")

        if mc.get("custom_instructions"):
            context_parts.append(f"Additional instructions: {mc['custom_instructions']}")

        if not context_parts:
            return ""

        return "User context: " + " ".join(context_parts)


class MagicLinkToken(Base):
    """Magic link tokens for passwordless authentication"""
    __tablename__ = "magic_link_tokens"

    id = Column(Integer, primary_key=True, autoincrement=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    token_type = Column(String(50), nullable=False)  # "login" or "verify"
    expires_at = Column(DateTime(timezone=True), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index('idx_magic_link_email_type', 'email', 'token_type'),
        Index('idx_magic_link_expires', 'expires_at'),
    )
