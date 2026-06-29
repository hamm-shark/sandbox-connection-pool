import asyncio

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine

from src.main.app_config import get_settings, AppSettings
from pool_monitoring.monitor import monitor
from pool_monitoring.plot_connections import get_plot
from src.infra.postgres.pg import engine
from pool_monitoring.monitor_summary import build_connections_summary, build_hold_times_summary
from pool_monitoring.monitoring_settings import (
    CSV_FILE,
    BASE_DIR,
    SUMMARY_FILE,
    POOL_MONITOR_FILE,
    SUMMARY_POOL_MONITOR_FILE,
    SAMPLES_PER_RUN,
    TOTAL_CONN_MIN,
    PGBOUNCER_PORT,
)


def get_test_name(settings: AppSettings) -> str:
    endpoint_type = settings.ENDPOINT_TYPE
    default_name = "ConnPoolSA"
    if settings.db.PORT == PGBOUNCER_PORT:
        default_name = "ConnPoolPgBouncer"
    if settings.USE_PGBOUNCER_CONN_POOL:
        default_name += "_NullPool"
    else:
        default_name += "_AsyncAdaptedQueuePool"
    return f"{default_name}: {endpoint_type}"


async def run(sa_engine: AsyncEngine, app_settings: AppSettings):
    print("Start pool monitoring")
    try:
        await monitor(sa_engine, get_test_name(app_settings), TOTAL_CONN_MIN)
    except OperationalError:
        print("Database is unavailable")
    finally:
        print("Building plot...")
        await build_connections_summary(samples_per_run=SAMPLES_PER_RUN, input_file=CSV_FILE, output_file=SUMMARY_FILE)
        await build_hold_times_summary(input_file=POOL_MONITOR_FILE, output_file=SUMMARY_POOL_MONITOR_FILE)
        await get_plot(CSV_FILE, BASE_DIR)
        await get_plot(SUMMARY_FILE, BASE_DIR, is_avg=True)
        await sa_engine.dispose()


try:
    asyncio.run(run(engine, get_settings(AppSettings)))
except KeyboardInterrupt:
    print("Interrupted by user")
