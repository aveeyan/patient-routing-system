# db/session.py

"""Database Session"""

# Third Party Imports
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Local Imports
from core.config import settings


## DB Engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=True,
)

## Session Factory
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


## Dependency
async def get_db() -> AsyncSession:
    """Yield an async database session. For use as a FastAPI dependency."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.error("Database session error, rolling back", error=str(exc))
            raise
