"""
Team API Routes — CRUD and member management within organizations.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.guards import get_current_active_user
from app.database import get_db
from app.models.team import TeamMemberRole
from app.models.user import User
from app.repositories.organization_repository import OrganizationRepository
from app.repositories.team_repository import TeamRepository
from app.schemas.team import (
    AddTeamMemberRequest,
    PaginatedTeams,
    TeamCreate,
    TeamResponse,
    TeamUpdate,
    UpdateTeamMemberRoleRequest,
)

router = APIRouter(prefix="/organizations/{org_id}/teams", tags=["Teams"])


async def _get_team_or_404(repo: TeamRepository, team_id: uuid.UUID) -> object:
    team = await repo.get_by_id(team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team not found.")
    return team


# ─── Create Team ───────────────────────────────────────────────────────────────
@router.post(
    "/",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a team in an organization",
)
async def create_team(
    org_id: uuid.UUID,
    payload: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamResponse:
    org_repo = OrganizationRepository(db)
    if not await org_repo.is_member(org_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not an organization member.")

    team_repo = TeamRepository(db)
    if await team_repo.slug_exists_in_org(org_id, payload.slug):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Team slug '{payload.slug}' already exists in this organization.",
        )

    team = await team_repo.create(
        organization_id=org_id,
        name=payload.name,
        slug=payload.slug,
        description=payload.description,
        is_private=payload.is_private,
    )
    # Add creator as lead
    await team_repo.add_member(
        team_id=team.id,
        user_id=current_user.id,
        role=TeamMemberRole.LEAD,
        added_by_id=current_user.id,
    )
    count = await team_repo.count_members(team.id)
    resp = TeamResponse.model_validate(team)
    resp.member_count = count
    return resp


# ─── List Teams ────────────────────────────────────────────────────────────────
@router.get("/", response_model=PaginatedTeams, summary="List teams in organization")
async def list_teams(
    org_id: uuid.UUID,
    page: int = 1,
    size: int = 20,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    import math
    org_repo = OrganizationRepository(db)
    if not await org_repo.is_member(org_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    team_repo = TeamRepository(db)
    skip = (page - 1) * size
    teams, total = await team_repo.list_by_org(org_id, skip=skip, limit=size)

    items = []
    for t in teams:
        resp = TeamResponse.model_validate(t)
        resp.member_count = await team_repo.count_members(t.id)
        items.append(resp)

    return {
        "items": items, "total": total, "page": page, "size": size,
        "pages": math.ceil(total / size) if total > 0 else 0,
    }


# ─── Get / Update / Delete Team ───────────────────────────────────────────────
@router.get("/{team_id}", response_model=TeamResponse, summary="Get team by ID")
async def get_team(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamResponse:
    org_repo = OrganizationRepository(db)
    if not await org_repo.is_member(org_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    team_repo = TeamRepository(db)
    team = await _get_team_or_404(team_repo, team_id)
    resp = TeamResponse.model_validate(team)
    resp.member_count = await team_repo.count_members(team_id)
    return resp


@router.patch("/{team_id}", response_model=TeamResponse, summary="Update team")
async def update_team(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    payload: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> TeamResponse:
    team_repo = TeamRepository(db)
    member = await team_repo.get_member(team_id, current_user.id)
    if member is None or member.role != TeamMemberRole.LEAD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team Lead required.")

    team = await team_repo.update(team_id, **payload.model_dump(exclude_none=True))
    resp = TeamResponse.model_validate(team)
    resp.member_count = await team_repo.count_members(team_id)
    return resp


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    team_repo = TeamRepository(db)
    member = await team_repo.get_member(team_id, current_user.id)
    if member is None or member.role != TeamMemberRole.LEAD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team Lead required.")
    await team_repo.delete(team_id)


# ─── Team Member Management ────────────────────────────────────────────────────
@router.get("/{team_id}/members", summary="List team members")
async def list_team_members(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    team_repo = TeamRepository(db)
    if not await team_repo.is_member(team_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a team member.")
    members, total = await team_repo.list_members(team_id)
    return {"items": members, "total": total}


@router.post("/{team_id}/members", status_code=status.HTTP_201_CREATED, summary="Add a team member")
async def add_team_member(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    payload: AddTeamMemberRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    team_repo = TeamRepository(db)
    me = await team_repo.get_member(team_id, current_user.id)
    if me is None or me.role != TeamMemberRole.LEAD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team Lead required.")

    if await team_repo.is_member(team_id, payload.user_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User is already a team member.")

    await team_repo.add_member(
        team_id=team_id,
        user_id=payload.user_id,
        role=payload.role,
        added_by_id=current_user.id,
    )
    return {"message": "Member added successfully."}


@router.patch("/{team_id}/members/{user_id}", summary="Update team member role")
async def update_team_member_role(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    payload: UpdateTeamMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    team_repo = TeamRepository(db)
    me = await team_repo.get_member(team_id, current_user.id)
    if me is None or me.role != TeamMemberRole.LEAD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team Lead required.")
    updated = await team_repo.update_member_role(team_id, user_id, payload.role)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
    return {"message": f"Role updated to {payload.role}."}


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    org_id: uuid.UUID,
    team_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    team_repo = TeamRepository(db)
    me = await team_repo.get_member(team_id, current_user.id)
    if me is None or me.role != TeamMemberRole.LEAD:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Team Lead required.")
    removed = await team_repo.remove_member(team_id, user_id)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found.")
