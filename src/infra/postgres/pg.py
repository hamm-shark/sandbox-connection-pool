import contextlib
import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main.app_config import AppSettings, get_settings

logger = logging.getLogger(__name__)


engine: AsyncEngine = create_async_engine(
    get_settings(AppSettings).db.dsn,
    echo=get_settings(AppSettings).db.ECHO,
    connect_args={"connect_timeout": get_settings(AppSettings).db.TIMEOUT},
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,
)

async_session_factory = async_sessionmaker(engine, autoflush=False, expire_on_commit=False, class_=AsyncSession)


@contextlib.asynccontextmanager
async def transaction(rollback: bool = True) -> AsyncGenerator[AsyncSession, Any]:
    async with async_session_factory() as session, session.begin():
        try:
            yield session
        except Exception as ex:
            if rollback:
                raise
            else:
                logger.exception(f"Transaction failed with {ex}")
