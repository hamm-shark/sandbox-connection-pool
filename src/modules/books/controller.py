from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import select

from src.infra.postgres.models.author import Author
from src.infra.postgres.models.book import Book
from src.infra.postgres.transaction_manager import PostgresTrManagerDep
from src.main.enums import BookStatus
from src.modules.base.controller import BaseController
from src.modules.books.schemas import BookCreateRequest, BookResponse


class BookController(BaseController):
    async def read_books(self) -> list[BookResponse]:
        return await self.tr_manager.book.read_books()

    async def create_book(self, body: BookCreateRequest) -> BookResponse:
        author_ids = body.authors
        result = await self.tr_manager.session.execute(select(Author).where(Author.id.in_(author_ids)))
        authors_by_id = {author.id: author for author in result.scalars().all()}
        missing_ids = [author_id for author_id in author_ids if author_id not in authors_by_id]

        for author_id in missing_ids:
            # Request contains only author ids, so create a placeholder name for new records.
            author = Author(id=author_id, name=f"Author {author_id}")
            self.tr_manager.session.add(author)
            authors_by_id[author_id] = author

        authors = [authors_by_id[author_id] for author_id in author_ids]

        book = await self.tr_manager.book.create(
            Book(
                title=body.title,
                genre=body.genre,
                status=BookStatus.CREATED,
                authors=authors,
            ),
        )
        return BookResponse.model_validate(book)


async def get_controller(tr_manager: PostgresTrManagerDep) -> AsyncIterator[BookController]:
    yield BookController(tr_manager=tr_manager)


BookControllerDep = Annotated[BookController, Depends(get_controller)]
