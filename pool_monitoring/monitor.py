import asyncio

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from pool_monitoring.monitoring_settings import CSV_FILE, HEADERS


if not CSV_FILE.exists():
    CSV_FILE.write_text(HEADERS)


async def monitor(sa_engine: AsyncEngine, test_name: str) -> None:
    last = None
    total_conn_min = 5
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
            current = (active, idle, idle_tx)
            if current == last or total < total_conn_min:
                continue
            last = current

            with CSV_FILE.open("a") as f:
                f.write(f"{test_name},{total},{active},{idle},{idle_tx}\n")

        await asyncio.sleep(1)
