"""
User Profile API Routes.
"""
import uuid
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user, get_current_superuser
from app.database import get_db
from app.models.user import User
from app.schemas.user import (
    ChangePasswordRequest,
    PaginatedUsers,
    UpdateProfileRequest,
    UserProfile,
    UserPublic,
)
from app.services.user_service import UserService
from app.services.token_service import TokenService

router = APIRouter(prefix="/users", tags=["Users"])


# ─── My Profile ────────────────────────────────────────────────────────────────
@router.get(
    "/me",
    response_model=UserProfile,
    summary="Get my profile",
)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
) -> User:
    return current_user


@router.patch(
    "/me",
    response_model=UserProfile,
    summary="Update my profile",
    description="Partially update profile fields. Only provided fields are updated.",
)
async def update_my_profile(
    payload: UpdateProfileRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> User:
    service = UserService(db)
    return await service.update_profile(current_user.id, payload)


@router.post(
    "/me/change-password",
    summary="Change password",
    description=(
        "Changes the user's password. Requires current password verification. "
        "Revokes all active sessions after password change."
    ),
)
async def change_password(
    payload: ChangePasswordRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    token_service = TokenService(db)
    service = UserService(db)
    return await service.change_password(current_user.id, payload, token_service)


@router.delete(
    "/me",
    summary="Deactivate my account",
    status_code=status.HTTP_200_OK,
)
async def deactivate_my_account(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    service = UserService(db)
    return await service.deactivate_account(current_user.id)


# ─── Public User Profiles ──────────────────────────────────────────────────────
@router.get(
    "/{user_id}",
    response_model=UserPublic,
    summary="Get public user profile",
)
async def get_user_public(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_active_user),
) -> User:
    service = UserService(db)
    return await service.get_profile(user_id)


# ─── Admin ─────────────────────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=PaginatedUsers,
    summary="[Admin] List all users",
)
async def list_all_users(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_superuser),
) -> dict:
    service = UserService(db)
    return await service.list_users(page=page, size=size)
