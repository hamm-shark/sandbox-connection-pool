from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.postgres.models import Author, Book, M2MBooksAuthors
from src.main.app_config import AppSettings, get_settings
from src.main.enums import BookStatus
from src.modules.base.controller import BookPaymentBaseController


class BookPaymentSeedController(BookPaymentBaseController):
    def __init__(self, app_settings: AppSettings) -> None:
        super().__init__(app_settings)

    async def seed_authors_with_books(
        self,
        *,
        session: AsyncSession,
        authors_count: int,
        books_per_author: int,
    ) -> tuple[int, int]:
        created_authors = 0
        created_books = 0
        for _ in range(authors_count):
            author = Author(name=self.faker.name())
            session.add(author)
            created_authors += 1

            for _ in range(books_per_author):
                book = Book(
                    title=self.faker.sentence(nb_words=4).rstrip("."),
                    genre=self.faker.word(),
                    status=BookStatus.CREATED,
                    authors=[author],
                )
                session.add(book)
                created_books += 1

        await self.session_flush(session)
        return created_authors, created_books

    async def clean_db(self, *, session: AsyncSession) -> tuple[int, int]:
        books_deleted = (await session.scalar(select(func.count()).select_from(Book))) or 0
        authors_deleted = (await session.scalar(select(func.count()).select_from(Author))) or 0
        await session.execute(delete(M2MBooksAuthors))
        await session.execute(delete(Book))
        await session.execute(delete(Author))
        await self.session_flush(session)
        return authors_deleted, books_deleted


async def get_controller() -> AsyncIterator[BookPaymentSeedController]:
    yield BookPaymentSeedController(app_settings=get_settings(AppSettings))


BookPaymentSeedControllerDep = Annotated[BookPaymentSeedController, Depends(get_controller)]
