"""
Token Service — creates, validates, and revokes JWT + refresh tokens.
Bridges core/security (stateless) with the UserRepository (stateful).
"""
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
)
from app.repositories.user_repository import UserRepository
from app.schemas.auth import TokenPair, AccessTokenResponse
from app.models.user import User, RefreshToken


class TokenService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    async def generate_token_pair(
        self,
        user: User,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> TokenPair:
        """
        Generate a new access + refresh token pair for a user.
        Persists the refresh token hash to the database.
        """
        access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "plan": user.plan.value},
        )
        raw_refresh_token = create_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS
        )

        await self.user_repo.create_refresh_token(
            user_id=user.id,
            raw_token=raw_refresh_token,
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )

        return TokenPair(
            access_token=access_token,
            refresh_token=raw_refresh_token,
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
        )

    async def refresh_access_token(
        self, raw_refresh_token: str
    ) -> tuple[AccessTokenResponse, RefreshToken]:
        """
        Exchange a valid refresh token for a new access token.
        Does NOT rotate the refresh token (add rotation logic here if needed).

        Returns:
            (AccessTokenResponse, RefreshToken) — caller can get the user from token.user_id.

        Raises:
            ValueError: If the token is invalid, expired, or revoked.
        """
        stored_token = await self.user_repo.get_refresh_token(raw_refresh_token)
        if stored_token is None:
            raise ValueError("Invalid or expired refresh token.")

        user = await self.user_repo.get_by_id(stored_token.user_id)
        if user is None or not user.is_active:
            raise ValueError("User account not found or is inactive.")

        new_access_token = create_access_token(
            subject=str(user.id),
            extra_claims={"email": user.email, "plan": user.plan.value},
        )

        return (
            AccessTokenResponse(
                access_token=new_access_token,
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
            stored_token,
        )

    async def revoke_refresh_token(self, raw_refresh_token: str) -> bool:
        """Revoke a single refresh token (logout from one device)."""
        return await self.user_repo.revoke_refresh_token(raw_refresh_token)

    async def revoke_all_tokens(self, user_id: uuid.UUID) -> int:
        """Revoke all refresh tokens for a user (logout all devices)."""
        return await self.user_repo.revoke_all_user_tokens(user_id)
