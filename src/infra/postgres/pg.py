import contextlib
import logging
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Any

from pool_monitoring.monitor import register_pool_monitoring
from pool_monitoring.monitoring_settings import POOL_MONITOR_FILE
from sqlalchemy import AsyncAdaptedQueuePool, NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.main.app_config import AppSettings, get_settings

logger = logging.getLogger(__name__)


def get_sa_engine(app_settings: AppSettings, monit_file: Path) -> AsyncEngine:
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
            echo=app_settings.db.ECHO,
        )

    if app_settings.POOL_OBSERVABILITY:
        register_pool_monitoring(
            sa_engine=sa_engine,
            output_file=monit_file,
        )

    return sa_engine


engine = get_sa_engine(get_settings(AppSettings), POOL_MONITOR_FILE)

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
