import asyncio
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from src.main.app_config import get_settings, AppSettings
from src.infra.postgres.pg import engine

CSV_FILE = Path("connections.csv")

app_settings = get_settings(AppSettings)


def get_test_name(settings: AppSettings) -> str:
    endpoint_type = settings.ENDPOINT_TYPE
    default_name = "SAConnPool"
    if settings.db.PORT == 6432:
        default_name = "pgBouncerConnPool"
    if settings.USE_PGBOUNCER_CONN_POOL:
        default_name += "_NullPool"
    else:
        default_name += "_AsyncAdaptedQueuePool"
    return f"{default_name}: {endpoint_type}"


if not CSV_FILE.exists():
    CSV_FILE.write_text("test,process_stat,total_connections,active,idle,idle_in_transaction\n")


async def monitor(sa_engine: AsyncEngine, test_name: str) -> None:
    print("Start pool monitoring")
    last = None
    while True:
        async with AsyncSession(sa_engine) as session:
            result = await session.execute(
                text("""
                    SELECT
                        count(*) AS total,
                        count(*) FILTER (WHERE state = 'active') AS active,
                        count(*) FILTER (WHERE state = 'idle') AS idle,
                        count(*) FILTER (WHERE state = 'idle in transaction') AS idle_tx
                    FROM pg_stat_activity
                    WHERE datname = current_database();
                """)
            )

            total, active, idle, idle_tx = result.one()
            current = (total, active, idle, idle_tx)
            if current == last:
                continue
            last = current

            with CSV_FILE.open("a") as f:
                f.write(f"{test_name},{total},{active},{idle},{idle_tx}\n")

        await asyncio.sleep(1)


try:
    asyncio.run(monitor(engine, get_test_name(app_settings)))
except KeyboardInterrupt:
    print("Stopping pool monitoring...")
    asyncio.run(engine.dispose())
