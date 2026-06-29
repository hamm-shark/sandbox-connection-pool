import asyncio
import csv
import time
from pathlib import Path

from sqlalchemy import text, event
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine

from pool_monitoring.monitoring_settings import CSV_FILE, HEADERS

if not CSV_FILE.exists():
    CSV_FILE.write_text(HEADERS)


async def monitor(sa_engine: AsyncEngine, test_name: str, total_conn_min: int) -> None:
    last = None
    while True:
        async with AsyncSession(sa_engine) as session:
            result = await session.execute(
                text("""
                     SELECT count(*) AS total,
                            count(*)    FILTER (WHERE state = 'active') AS active, count(*) FILTER (WHERE state = 'idle') AS idle, count(*) FILTER (WHERE state = 'idle in transaction') AS idle_tx
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


def register_pool_monitoring(sa_engine: AsyncEngine, output_file: Path) -> None:
    """Записывает время удержания соединения (connection hold time)."""
    hold_times: dict[int, float] = {}

    if not output_file.exists():
        with output_file.open("w", newline="") as f:
            csv.writer(f).writerow(["hold_time_ms"])

    @event.listens_for(sa_engine.sync_engine.pool, "checkout")
    def checkout(dbapi_conn, connection_record, connection_proxy):
        """SQLAlchemy выдал соединение из пула"""
        hold_times[id(dbapi_conn)] = time.perf_counter()

    @event.listens_for(sa_engine.sync_engine.pool, "checkin")
    def checkin(dbapi_conn, connection_record):
        """Cоединение вернулось обратно в пул"""
        started = hold_times.pop(id(dbapi_conn), None)
        if started is None:
            return

        elapsed_ms = (
            time.perf_counter() - started
        ) * 1000  # Сколько времени соединение было недоступно для других запросов

        with output_file.open("a", newline="") as f:
            csv.writer(f).writerow([round(elapsed_ms, 3)])
