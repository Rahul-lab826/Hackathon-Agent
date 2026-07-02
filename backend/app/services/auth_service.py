"""
Authentication Service — core business logic for registration, login, and logout.
Orchestrates UserRepository + TokenService + security utilities.
"""
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import AuthProvider, User
from app.repositories.user_repository import UserRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    TokenPair,
    AccessTokenResponse,
    MessageResponse,
)
from app.services.token_service import TokenService

# Lock an account after this many consecutive failed logins
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.token_service = TokenService(db)

    async def register(
        self, payload: RegisterRequest, request: Request | None = None
    ) -> TokenPair:
        """
        Register a new user with email + password.
        - Validates email uniqueness
        - Hashes the password (bcrypt)
        - Creates the user record
        - Returns a token pair immediately (auto-login after registration)
        """
        # 1. Uniqueness check
        if await self.user_repo.email_exists(payload.email.lower()):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="An account with this email already exists.",
            )

        # 2. Create user
        user = await self.user_repo.create(
            email=payload.email.lower(),
            hashed_password=hash_password(payload.password),
            full_name=payload.full_name,
            auth_provider=AuthProvider.EMAIL.value,
            is_verified=False,   # Require email verification in production
        )

        # 3. Issue token pair
        ip = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        return await self.token_service.generate_token_pair(
            user, device_info=ua, ip_address=ip
        )

    async def login(
        self, payload: LoginRequest, request: Request | None = None
    ) -> TokenPair:
        """
        Authenticate a user with email + password.
        - Looks up user by email
        - Checks account lock status
        - Verifies password
        - Tracks failed attempts / locks account on repeated failures
        - Updates last_login timestamp
        - Returns a token pair
        """
        user = await self.user_repo.get_by_email(payload.email.lower())

        # Generic error — don't reveal whether the email exists
        invalid_credentials = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

        if user is None:
            raise invalid_credentials

        # Check account lock
        if user.locked_until and user.locked_until > datetime.now(timezone.utc):
            remaining = int((user.locked_until - datetime.now(timezone.utc)).total_seconds() / 60)
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"Account temporarily locked. Try again in {remaining} minute(s).",
            )

        # Verify password (OAuth-only users have no password)
        if user.hashed_password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This account uses Google login. Please sign in with Google.",
            )

        if not verify_password(payload.password, user.hashed_password):
            new_count = await self.user_repo.increment_failed_logins(user.id)
            if new_count >= MAX_FAILED_ATTEMPTS:
                locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                await self.user_repo.lock_account(user.id, locked_until)
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail=f"Too many failed attempts. Account locked for {LOCKOUT_DURATION_MINUTES} minutes.",
                )
            remaining = MAX_FAILED_ATTEMPTS - new_count
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid email or password. {remaining} attempt(s) remaining.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check active status
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated. Please contact support.",
            )

        # Record successful login
        await self.user_repo.update_last_login(user.id)

        ip = request.client.host if request and request.client else None
        ua = request.headers.get("user-agent") if request else None
        return await self.token_service.generate_token_pair(
            user, device_info=ua, ip_address=ip
        )

    async def logout(self, raw_refresh_token: str) -> MessageResponse:
        """Revoke the provided refresh token (single-device logout)."""
        revoked = await self.token_service.revoke_refresh_token(raw_refresh_token)
        if not revoked:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Refresh token not found or already revoked.",
            )
        return MessageResponse(message="Logged out successfully.")

    async def logout_all_devices(self, user_id) -> MessageResponse:
        """Revoke ALL refresh tokens for a user (all-device logout)."""
        count = await self.token_service.revoke_all_tokens(user_id)
        return MessageResponse(message=f"Logged out from {count} device(s).")

    async def refresh_token(self, raw_refresh_token: str) -> AccessTokenResponse:
        """Exchange a valid refresh token for a new access token."""
        try:
            access_resp, _ = await self.token_service.refresh_access_token(raw_refresh_token)
            return access_resp
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
