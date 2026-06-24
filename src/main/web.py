import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI

from src.infra.postgres.pg import engine
from src.main.app_config import AppSettings, get_settings
from src.main.logging_config import configure_logging
from src.main.routers import init_routers

logger = logging.getLogger("app")


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    logger.info("Application is starting...")
    logger.info("Application has started")
    yield
    await engine.dispose()
    logger.info("Application has stopped")


def create_app() -> FastAPI:
    settings: AppSettings = get_settings(AppSettings)
    configure_logging(settings.LOG_LEVEL)
    app = FastAPI(
        lifespan=lifespan,
        docs_url="/api/docs" if settings.DEBUG else None,
    )
    init_routers(app)
    return app
