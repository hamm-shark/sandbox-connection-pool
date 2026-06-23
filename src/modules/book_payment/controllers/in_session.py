from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.postgres.models import Book
from src.infra.postgres.pg import transaction
from src.main.app_config import AppSettings, get_settings
from src.modules.base.controller import BookPaymentBaseController, PaymentError


class BookPaymentInSessionController(BookPaymentBaseController):
    def __init__(self, app_settings: AppSettings) -> None:
        super().__init__(app_settings)

    async def worker(self) -> list[Book]:
        async with transaction() as session:
            return await self.get_books(session=session)

    async def worker_for_update(self) -> list[Book]:
        async with transaction() as session:
            return await self.update_books(session=session)

    async def get_books(self, *, session: AsyncSession) -> list[Book]:
        books = await self.read_books(session=session)
        await self.call_billing()
        await self.do_household_chores()
        return books

    async def sync_books(self, *, session: AsyncSession, books: list[Book]) -> None:
        try:
            await self.do_payment()
        except PaymentError as err:
            raise HTTPException(
                status_code=400,
                detail=err.message,
            ) from err
        await self.update_books_status(session=session, books=books)
        await self.session_commit(session=session)

    async def update_books(self, *, session: AsyncSession) -> list[Book]:
        books = await self.read_books(session=session)
        await self.sync_books(session=session, books=books)
        await self.do_household_chores()
        return await self.read_books(session=session)


async def get_controller() -> AsyncIterator[BookPaymentInSessionController]:
    yield BookPaymentInSessionController(app_settings=get_settings(AppSettings))


BookPaymentInSessionControllerDep = Annotated[BookPaymentInSessionController, Depends(get_controller)]
