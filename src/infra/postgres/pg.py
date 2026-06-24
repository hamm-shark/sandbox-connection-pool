import contextlib
import logging
from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main.app_config import AppSettings, get_settings

logger = logging.getLogger(__name__)


def get_async_engine() -> AsyncEngine:
    sa_engine = create_async_engine(
        get_settings(AppSettings).db.dsn,
        echo=get_settings(AppSettings).db.ECHO,
        connect_args={"connect_timeout": get_settings(AppSettings).db.TIMEOUT},
        poolclass=AsyncAdaptedQueuePool,
        pool_size=get_settings(AppSettings).conn_pool.POOL_SIZE,
        max_overflow=get_settings(AppSettings).conn_pool.MAX_OVERFLOW,
        pool_timeout=get_settings(AppSettings).conn_pool.POOL_TIMEOUT,
        pool_recycle=get_settings(AppSettings).conn_pool.POOL_RECYCLE,
    )

    if not get_settings(AppSettings).USE_SA_CONNECTION_POOL:
        sa_engine = create_async_engine(
            get_settings(AppSettings).db.dsn,
            poolclass=NullPool,
        )
    return sa_engine


engine = get_async_engine()

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
