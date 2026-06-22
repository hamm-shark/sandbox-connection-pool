from types import TracebackType
from typing import Annotated, Self, TypeVar

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    AsyncSessionTransaction,
    async_sessionmaker,
)

from src.infra.postgres.pg import async_session_factory
from src.infra.postgres.storage.book import BookStorage

TExc = TypeVar("TExc", bound=BaseException)


class TransactionManager:
    session: AsyncSession
    session_factory: async_sessionmaker[AsyncSession]
    transaction: AsyncSessionTransaction
    book: BookStorage

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self.session_factory = session_factory

    async def __aenter__(self) -> Self:
        self.session = self.session_factory()
        self.book = BookStorage(self.session)
        self.transaction: AsyncSessionTransaction = await self.session.begin()
        return self

    async def __aexit__(self, exc_type: type[TExc] | None, exc: TExc | None, traceback: TracebackType | None) -> None:  # noqa: PYI036
        if exc_type is None:
            await self.commit()
        else:
            await self.transaction.rollback()
        await self.session.close()

    async def commit(self) -> None:
        await self.transaction.commit()


async def get_tr_manager() -> TransactionManager:
    return TransactionManager(async_session_factory)


PostgresTrManagerDep = Annotated[TransactionManager, Depends(get_tr_manager)]
