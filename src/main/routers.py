from fastapi import FastAPI

from src.modules.root_router import router


def init_routers(app: FastAPI) -> None:
    app.include_router(router)
