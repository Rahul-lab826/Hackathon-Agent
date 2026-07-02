"""
Organization Repository — database operations for Organizations and their Members.
"""
import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.organization import Organization, OrganizationMember, OrgMemberRole


class OrganizationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ─── Organization CRUD ─────────────────────────────────────────────────────

    async def create(
        self,
        name: str,
        slug: str,
        description: str | None = None,
        website: str | None = None,
        industry: str | None = None,
        location: str | None = None,
    ) -> Organization:
        org = Organization(
            name=name,
            slug=slug,
            description=description,
            website=website,
            industry=industry,
            location=location,
        )
        self.db.add(org)
        await self.db.flush()
        await self.db.refresh(org)
        return org

    async def get_by_id(self, org_id: uuid.UUID) -> Organization | None:
        result = await self.db.execute(
            select(Organization)
            .where(Organization.id == org_id)
            .options(selectinload(Organization.members))
        )
        return result.scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Organization | None:
        result = await self.db.execute(
            select(Organization).where(Organization.slug == slug)
        )
        return result.scalar_one_or_none()

    async def slug_exists(self, slug: str) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(Organization).where(Organization.slug == slug)
        )
        return (result.scalar() or 0) > 0

    async def update(self, org_id: uuid.UUID, **kwargs) -> Organization | None:
        await self.db.execute(
            update(Organization)
            .where(Organization.id == org_id)
            .values(**kwargs, updated_at=datetime.now(timezone.utc))
        )
        return await self.get_by_id(org_id)

    async def delete(self, org_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(Organization).where(Organization.id == org_id)
        )
        return result.rowcount > 0

    async def list_by_user(
        self, user_id: uuid.UUID, skip: int = 0, limit: int = 20
    ) -> tuple[list[Organization], int]:
        """List organizations where the user is a member."""
        subq = (
            select(OrganizationMember.organization_id)
            .where(OrganizationMember.user_id == user_id)
            .subquery()
        )
        count_result = await self.db.execute(
            select(func.count()).select_from(Organization).where(Organization.id.in_(subq))
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(Organization)
            .where(Organization.id.in_(subq))
            .offset(skip)
            .limit(limit)
            .order_by(Organization.created_at.desc())
        )
        return list(result.scalars().all()), total

    # ─── Member Management ─────────────────────────────────────────────────────

    async def add_member(
        self,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        role: OrgMemberRole = OrgMemberRole.MEMBER,
        invited_by_id: uuid.UUID | None = None,
        accepted: bool = False,
    ) -> OrganizationMember:
        member = OrganizationMember(
            organization_id=org_id,
            user_id=user_id,
            role=role,
            invited_by_id=invited_by_id,
            accepted_at=datetime.now(timezone.utc) if accepted else None,
        )
        self.db.add(member)
        await self.db.flush()
        return member

    async def get_member(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrganizationMember | None:
        result = await self.db.execute(
            select(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def update_member_role(
        self, org_id: uuid.UUID, user_id: uuid.UUID, role: OrgMemberRole
    ) -> bool:
        result = await self.db.execute(
            update(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
            .values(role=role)
        )
        return result.rowcount > 0

    async def remove_member(self, org_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            delete(OrganizationMember).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def list_members(
        self, org_id: uuid.UUID, skip: int = 0, limit: int = 50
    ) -> tuple[list[OrganizationMember], int]:
        count_result = await self.db.execute(
            select(func.count())
            .select_from(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
        )
        total = count_result.scalar() or 0

        result = await self.db.execute(
            select(OrganizationMember)
            .where(OrganizationMember.organization_id == org_id)
            .offset(skip)
            .limit(limit)
            .order_by(OrganizationMember.created_at.asc())
        )
        return list(result.scalars().all()), total

    async def is_member(self, org_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.db.execute(
            select(func.count())
            .select_from(OrganizationMember)
            .where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return (result.scalar() or 0) > 0

    async def get_member_role(
        self, org_id: uuid.UUID, user_id: uuid.UUID
    ) -> OrgMemberRole | None:
        result = await self.db.execute(
            select(OrganizationMember.role).where(
                OrganizationMember.organization_id == org_id,
                OrganizationMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()
