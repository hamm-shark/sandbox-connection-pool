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


def get_sa_engine(app_settings: AppSettings) -> AsyncEngine:
    db_dsn = app_settings.db.dsn
    sa_engine = create_async_engine(
        db_dsn,
        echo=app_settings.db.ECHO,
        connect_args={"connect_timeout": app_settings.db.TIMEOUT},
        poolclass=AsyncAdaptedQueuePool,
        pool_size=app_settings.conn_pool.POOL_SIZE,
        max_overflow=app_settings.conn_pool.MAX_OVERFLOW,
        pool_timeout=app_settings.conn_pool.POOL_TIMEOUT,
        pool_recycle=app_settings.conn_pool.POOL_RECYCLE,
    )

    if app_settings.USE_PGBOUNCER_CONN_POOL:
        sa_engine = create_async_engine(
            db_dsn,
            poolclass=NullPool,
        )
    return sa_engine


engine = get_sa_engine(get_settings(AppSettings))

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
