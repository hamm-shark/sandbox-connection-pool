from typing import TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.postgres.models.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class PostgresStorage[ModelT]:
    model_cls: type[ModelT]

    def __init__(self, db: AsyncSession) -> None:
        self._db: AsyncSession = db
