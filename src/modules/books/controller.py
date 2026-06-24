from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from src.infra.postgres.transaction_manager import PostgresTrManagerDep
from src.modules.base.controller import BaseController
from src.modules.books.schemas import BookCreateRequest, BookResponse


class BookController(BaseController):
    async def read_books(self) -> list[BookResponse]:
        async with self.tr_manager as mng:
            return await mng.book.read_books()

    async def create_book(self, body: BookCreateRequest) -> BookResponse:
        async with self.tr_manager as mng:
            book = await mng.book.create(data=body)
        return BookResponse(
            id=book.id,
            title=book.title,
            genre=book.genre,
            authors=[author.id for author in book.authors],
        )


async def get_controller(tr_manager: PostgresTrManagerDep) -> AsyncIterator[BookController]:
    yield BookController(tr_manager=tr_manager)


BookControllerDep = Annotated[BookController, Depends(get_controller)]
