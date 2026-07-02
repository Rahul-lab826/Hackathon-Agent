"""
User Repository — all database operations for User and RefreshToken models.
Follows the Repository pattern: services call this, never raw SQLAlchemy queries.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, RefreshToken
from app.core.security import hash_token


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── User CRUD ─────────────────────────────────────────────────────────────

    async def create(
        self,
        email: str,
        hashed_password: str | None,
        full_name: str | None = None,
        auth_provider: str = "email",
        google_id: str | None = None,
        avatar_url: str | None = None,
        is_verified: bool = False,
    ) -> User:
        """Create and persist a new user."""
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            auth_provider=auth_provider,
            google_id=google_id,
            avatar_url=avatar_url,
            is_verified=is_verified,
        )
        self.db.add(user)
        await self.db.flush()   # Get ID without full commit
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: uuid.UUID) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_google_id(self, google_id: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.google_id == google_id)
        )
        return result.scalar_one_or_none()

    async def update(self, user_id: uuid.UUID, **kwargs) -> User | None:
        """Partial update — only provided kwargs are updated."""
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(**kwargs, updated_at=datetime.now(timezone.utc))
        )
        return await self.get_by_id(user_id)

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(
                last_login_at=datetime.now(timezone.utc),
                failed_login_attempts=0,
                locked_until=None,
            )
        )

    async def increment_failed_logins(self, user_id: uuid.UUID) -> int:
        """Increment failed login count. Returns the new count."""
        result = await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(failed_login_attempts=User.failed_login_attempts + 1)
            .returning(User.failed_login_attempts)
        )
        return result.scalar_one()

    async def lock_account(self, user_id: uuid.UUID, locked_until: datetime) -> None:
        await self.db.execute(
            update(User)
            .where(User.id == user_id)
            .values(locked_until=locked_until)
        )

    async def email_exists(self, email: str) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.email == email.lower())
        )
        return (result.scalar() or 0) > 0

    async def username_exists(self, username: str) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(User).where(User.username == username)
        )
        return (result.scalar() or 0) > 0

    async def list_users(
        self, skip: int = 0, limit: int = 20
    ) -> tuple[list[User], int]:
        """Return paginated users and total count."""
        count_result = await self.db.execute(
            select(func.count()).select_from(User)
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def delete(self, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(User).where(User.id == user_id)
        )
        return result.rowcount > 0

    # ─── Refresh Token CRUD ────────────────────────────────────────────────────

    async def create_refresh_token(
        self,
        user_id: uuid.UUID,
        raw_token: str,
        expires_at: datetime,
        device_info: str | None = None,
        ip_address: str | None = None,
    ) -> RefreshToken:
        """Hash and store a refresh token."""
        token = RefreshToken(
            user_id=user_id,
            token_hash=hash_token(raw_token),
            expires_at=expires_at,
            device_info=device_info,
            ip_address=ip_address,
        )
        self.db.add(token)
        await self.db.flush()
        return token

    async def get_refresh_token(self, raw_token: str) -> RefreshToken | None:
        """Lookup a refresh token by its raw value (hashed for comparison)."""
        result = await self.db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == hash_token(raw_token),
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke_refresh_token(self, raw_token: str) -> bool:
        """Revoke a single refresh token."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.token_hash == hash_token(raw_token))
            .values(is_revoked=True)
        )
        return result.rowcount > 0

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> int:
        """Revoke ALL refresh tokens for a user (e.g., on password change)."""
        result = await self.db.execute(
            update(RefreshToken)
            .where(
                RefreshToken.user_id == user_id,
                RefreshToken.is_revoked.is_(False),
            )
            .values(is_revoked=True)
        )
        return result.rowcount

    async def delete_expired_tokens(self) -> int:
        """Cleanup job — delete all expired tokens."""
        result = await self.db.execute(
            delete(RefreshToken).where(
                RefreshToken.expires_at < datetime.now(timezone.utc)
            )
        )
        return result.rowcount
