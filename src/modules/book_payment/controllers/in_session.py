from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.postgres.models import Book
from src.infra.postgres.pg import transaction
from src.main.app_config import AppSettings, get_settings
from src.modules.base.controller import BookPaymentBaseController
from src.modules.book_payment.schemas import BookResponse


class BookPaymentInSessionController(BookPaymentBaseController):
    def __init__(self, app_settings: AppSettings) -> None:
        super().__init__(app_settings)

    async def worker(self, limit: int) -> list[BookResponse]:
        async with transaction() as session:
            return await self.get_books(session=session, limit=limit)

    async def worker_for_update(self, limit: int) -> list[BookResponse]:
        async with transaction() as session:
            return await self.update_books(session=session, limit=limit)

    async def get_books(self, *, session: AsyncSession, limit: int) -> list[BookResponse]:
        books = await self.read_books(session=session, limit=limit)
        await self.call_billing()
        await self.call_domestic_service()
        return [BookResponse.model_validate(book) for book in books]

    async def sync_books(self, *, session: AsyncSession, books: list[Book]) -> list[Book]:
        await self.call_billing()
        updated_book_ids = await self.update_books_status(session=session, books=books)
        updated_books = await self.read_book_by_ids(session=session, book_ids=updated_book_ids)
        await self.session_commit(session=session)
        return updated_books

    async def update_books(self, *, session: AsyncSession, limit: int) -> list[BookResponse]:
        books = await self.read_books(session=session, limit=limit)
        updated_books = await self.sync_books(session=session, books=books)
        await self.call_domestic_service()
        return [BookResponse.model_validate(book) for book in updated_books]


async def get_controller() -> AsyncIterator[BookPaymentInSessionController]:
    yield BookPaymentInSessionController(app_settings=get_settings(AppSettings))


BookPaymentInSessionControllerDep = Annotated[BookPaymentInSessionController, Depends(get_controller)]
