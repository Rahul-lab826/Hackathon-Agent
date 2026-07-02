"""Team Repository — database operations for Teams and their Members."""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team, TeamMember, TeamMemberRole


class TeamRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Team CRUD ─────────────────────────────────────────────────────────────

    async def create(
        self,
        organization_id: uuid.UUID,
        name: str,
        slug: str,
        description: str | None = None,
        is_private: bool = False,
    ) -> Team:
        team = Team(
            organization_id=organization_id,
            name=name,
            slug=slug,
            description=description,
            is_private=is_private,
        )
        self.db.add(team)
        await self.db.flush()
        await self.db.refresh(team)
        return team

    async def get_by_id(self, team_id: uuid.UUID) -> Team | None:
        result = await self.db.execute(
            select(Team).where(Team.id == team_id)
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, org_id: uuid.UUID, slug: str) -> Team | None:
        result = await self.db.execute(
            select(Team).where(
                Team.organization_id == org_id,
                Team.slug == slug,
            )
        )
        return result.scalar_one_or_none()

    async def slug_exists_in_org(self, org_id: uuid.UUID, slug: str) -> bool:
        result = await self.db.execute(
            select(func.count())
            .select_from(Team)
            .where(Team.organization_id == org_id, Team.slug == slug)
        )
        return (result.scalar() or 0) > 0

    async def update(self, team_id: uuid.UUID, **kwargs) -> Team | None:
        await self.db.execute(
            update(Team)
            .where(Team.id == team_id)
            .values(**kwargs, updated_at=datetime.now(timezone.utc))
        )
        return await self.get_by_id(team_id)

    async def delete(self, team_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(Team).where(Team.id == team_id)
        )
        return result.rowcount > 0

    async def list_by_org(
        self, org_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Team], int]:
        count_result = await self.db.execute(
            select(func.count()).select_from(Team).where(Team.organization_id == org_id)
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(Team)
            .where(Team.organization_id == org_id, Team.is_active.is_(True))
            .offset(skip)
            .limit(limit)
            .order_by(Team.created_at.desc())
        )
        return list(result.scalars().all()), total

    async def count_members(self, team_id: uuid.UUID) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team_id)
        )
        return result.scalar() or 0

    # ─── Member Management ─────────────────────────────────────────────────────

    async def add_member(
        self,
        team_id: uuid.UUID,
        user_id: uuid.UUID,
        role: TeamMemberRole = TeamMemberRole.MEMBER,
        added_by_id: uuid.UUID | None = None,
    ) -> TeamMember:
        member = TeamMember(
            team_id=team_id,
            user_id=user_id,
            role=role,
            added_by_id=added_by_id,
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def get_member(
        self, team_id: uuid.UUID, user_id: uuid.UUID
    ) -> TeamMember | None:
        result = await self.db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_member_role(
        self, team_id: uuid.UUID, user_id: uuid.UUID, role: TeamMemberRole
    ) -> bool:
        result = await self.db.execute(
            update(TeamMember)
            .where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
            .values(role=role)
        )
        return result.rowcount > 0

    async def remove_member(self, team_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def list_members(
        self, team_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list[TeamMember], int]:
        count_result = await self.db.execute(
            select(func.count()).select_from(TeamMember).where(TeamMember.team_id == team_id)
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(TeamMember)
            .where(TeamMember.team_id == team_id)
            .offset(skip)
            .limit(limit)
            .order_by(TeamMember.created_at.asc())
        )
        return list(result.scalars().all()), total

    async def is_member(self, team_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(func.count())
            .select_from(TeamMember)
            .where(TeamMember.team_id == team_id, TeamMember.user_id == user_id)
        )
        return (result.scalar() or 0) > 0
