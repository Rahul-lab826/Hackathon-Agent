"""
Organization API Routes — CRUD and member management.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user
from app.database import get_db
from app.models.organization import OrgMemberRole
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository
from app.schemas.organization import (
    InviteMemberRequest,
    OrgMemberResponse,
    OrganizationCreate,
    OrganizationResponse,
    OrganizationUpdate,
    PaginatedOrganizations,
    UpdateMemberRoleRequest,
)

router = APIRouter(prefix="/organizations", tags=["Organizations"])


def _require_admin(role: OrgMemberRole | None) -> None:
    if role not in (OrgMemberRole.OWNER, OrgMemberRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin or Owner role required.",
        )


def _require_owner(role: OrgMemberRole | None) -> None:
    if role != OrgMemberRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Owner role required.",
        )


# ─── Create Organization ───────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=OrganizationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an organization",
)
async def create_organization(
    payload: OrganizationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse:
    repo = OrganizationRepository(db)

    if await repo.slug_exists(payload.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Organization slug '{payload.slug}' is already taken.",
        )

    org = await repo.create(**payload.model_dump())
    # Auto-add creator as OWNER
    await repo.add_member(
        org_id=org.id,
        user_id=current_user.id,
        role=OrgMemberRole.OWNER,
        accepted=True,
    )
    return OrganizationResponse.model_validate(org)


# ─── List My Organizations ─────────────────────────────────────────────────────
@router.get(
    "/",
    response_model=PaginatedOrganizations,
    summary="List my organizations",
)
async def list_my_organizations(
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    import math
    repo = OrganizationRepository(db)
    skip = (page - 1) * size
    orgs, total = await repo.list_by_user(current_user.id, skip=skip, limit=size)
    return {
        "items": [OrganizationResponse.model_validate(o) for o in orgs],
        "total": total,
        "page": page,
        "size": size,
        "pages": math.ceil(total / size) if total > 0 else 0,
    }


# ─── Get Organization ──────────────────────────────────────────────────────────
@router.get(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Get organization by ID",
)
async def get_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse:
    repo = OrganizationRepository(db)
    org = await repo.get_by_id(org_id)
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found.")
    if not await repo.is_member(org_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    return OrganizationResponse.model_validate(org)


# ─── Update Organization ───────────────────────────────────────────────────────
@router.patch(
    "/{org_id}",
    response_model=OrganizationResponse,
    summary="Update organization",
)
async def update_organization(
    org_id: uuid.UUID,
    payload: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> OrganizationResponse:
    repo = OrganizationRepository(db)
    role = await repo.get_member_role(org_id, current_user.id)
    _require_admin(role)
    org = await repo.update(org_id, **payload.model_dump(exclude_none=True))
    return OrganizationResponse.model_validate(org)


# ─── Delete Organization ───────────────────────────────────────────────────────
@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    repo = OrganizationRepository(db)
    role = await repo.get_member_role(org_id, current_user.id)
    _require_owner(role)
    await repo.delete(org_id)


# ─── Member Management ─────────────────────────────────────────────────────────
@router.get("/{org_id}/members", summary="List organization members")
async def list_members(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    repo = OrganizationRepository(db)
    if not await repo.is_member(org_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
    members, total = await repo.list_members(org_id)
    return {"items": members, "total": total}


@router.post("/{org_id}/members", status_code=status.HTTP_201_CREATED, summary="Invite a member")
async def invite_member(
    org_id: uuid.UUID,
    payload: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    repo = OrganizationRepository(db)
    role = await repo.get_member_role(org_id, current_user.id)
    _require_admin(role)
    # In production: send invitation email and create a pending member record
    return {"message": f"Invitation sent to {payload.email} with role {payload.role}."}


@router.patch("/{org_id}/members/{user_id}", summary="Update member role")
async def update_member_role(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: UpdateMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    repo = OrganizationRepository(db)
    role = await repo.get_member_role(org_id, current_user.id)
    _require_owner(role)
    updated = await repo.update_member_role(org_id, user_id, payload.role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    return {"message": f"Role updated to {payload.role}."}


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    repo = OrganizationRepository(db)
    role = await repo.get_member_role(org_id, current_user.id)
    _require_admin(role)
    removed = await repo.remove_member(org_id, user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
