from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from src.infra.postgres.models import Book
from src.infra.postgres.pg import transaction
from src.main.app_config import AppSettings, get_settings
from src.modules.base.controller import BookPaymentBaseController
from src.modules.book_payment.schemas import BookResponse


class BookPaymentOutSessionController(BookPaymentBaseController):
    def __init__(self, app_settings: AppSettings) -> None:
        super().__init__(app_settings)

    async def get_books(self) -> list[BookResponse]:
        async with transaction() as session:
            books = await self.read_books(session=session)
        await self.call_billing()
        await self.call_domestic_service()
        return [BookResponse.model_validate(book) for book in books]

    async def sync_books(self, *, books: list[Book]) -> None:
        await self.call_billing()
        async with transaction() as session:
            await self.update_books_status(session=session, books=books)
            await self.session_commit(session=session)

    async def update_books(self) -> list[BookResponse]:
        async with transaction() as session:
            books = await self.read_books(session=session)
        await self.sync_books(books=books)
        await self.call_domestic_service()
        return [BookResponse.model_validate(book) for book in books]


async def get_controller() -> AsyncIterator[BookPaymentOutSessionController]:
    yield BookPaymentOutSessionController(app_settings=get_settings(AppSettings))


BookPaymentOutSessionControllerDep = Annotated[BookPaymentOutSessionController, Depends(get_controller)]
