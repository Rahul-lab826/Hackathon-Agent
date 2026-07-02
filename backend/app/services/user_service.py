"""
User Service — business logic for profile management.
"""
import uuid
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UpdateProfileRequest, ChangePasswordRequest, UserProfile


class UserService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)

    async def get_profile(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    async def update_profile(
        self, user_id: uuid.UUID, payload: UpdateProfileRequest
    ) -> User:
        """Update mutable profile fields."""
        update_data = payload.model_dump(exclude_none=True)

        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="No fields provided for update.",
            )

        # Username uniqueness check
        if "username" in update_data:
            if await self.user_repo.username_exists(update_data["username"]):
                existing = await self.user_repo.get_by_username(update_data["username"])
                if existing and existing.id != user_id:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail="This username is already taken.",
                    )

        user = await self.user_repo.update(user_id, **update_data)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
        return user

    async def change_password(
        self,
        user_id: uuid.UUID,
        payload: ChangePasswordRequest,
        token_service=None,
    ) -> dict:
        """
        Change a user's password.
        - Verifies current password
        - Validates new password confirmation
        - Hashes new password
        - Revokes ALL refresh tokens (force re-login on all devices)
        """
        user = await self.user_repo.get_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

        if user.hashed_password is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot set a password for Google-authenticated accounts.",
            )

        if not verify_password(payload.current_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect.",
            )

        payload.validate_passwords_match()

        await self.user_repo.update(
            user_id, hashed_password=hash_password(payload.new_password)
        )

        # Revoke all sessions — user must re-login
        if token_service:
            await token_service.revoke_all_tokens(user_id)

        return {"message": "Password changed successfully. Please log in again."}

    async def deactivate_account(self, user_id: uuid.UUID) -> dict:
        await self.user_repo.update(user_id, is_active=False)
        return {"message": "Account deactivated."}

    async def list_users(self, page: int = 1, size: int = 20) -> dict:
        skip = (page - 1) * size
        users, total = await self.user_repo.list_users(skip=skip, limit=size)
        import math
        return {
            "items": users,
            "total": total,
            "page": page,
            "size": size,
            "pages": math.ceil(total / size) if total > 0 else 0,
        }
