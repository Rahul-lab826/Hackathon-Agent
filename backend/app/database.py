"""
Async SQLAlchemy database engine, session factory, and declarative base.
Uses connection pooling with NullPool for Alembic migrations.
"""
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, MappedColumn
from sqlalchemy import MetaData, inspect

from app.config import settings

# ─── Naming Convention ─────────────────────────────────────────────────────────
# Enforces consistent constraint names across all migrations
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

# ─── Engine ────────────────────────────────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DATABASE_ECHO,
    pool_size=settings.DATABASE_POOL_SIZE,
    max_overflow=settings.DATABASE_MAX_OVERFLOW,
    pool_pre_ping=True,         # Detect stale connections
    pool_recycle=3600,          # Recycle connections every hour
)

# ─── Session Factory ───────────────────────────────────────────────────────────
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,     # Objects remain accessible after commit
    autocommit=False,
    autoflush=False,
)

# Convenience alias used by background tasks (generation streaming)
async_session_factory = AsyncSessionLocal

# ─── Declarative Base ──────────────────────────────────────────────────────────
class Base(DeclarativeBase):
    """
    All ORM models inherit from this base.
    Metadata uses enforced naming conventions for Alembic autogenerate.
    """
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


# ─── Dependency ────────────────────────────────────────────────────────────────
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that provides a database session per request.
    Automatically commits on success, rolls back on exception, and closes the session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
