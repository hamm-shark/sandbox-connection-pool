from asyncio import sleep
from collections.abc import AsyncIterator
from random import SystemRandom as Random
from typing import Annotated, Any

from faker import Faker
from fastapi import Depends, HTTPException
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.postgres.models import Author, Book, M2MBooksAuthors
from src.infra.postgres.pg import transaction
from src.main.app_config import AppSettings, get_settings
from src.main.enums import BookStatus


class PaymentError(Exception):
    """Имитация ошибки платежного сервиса."""


class ClientCallController:
    def __init__(self, app_settings: AppSettings) -> None:
        self.app_settings = app_settings
        self.faker = Faker()

    @staticmethod
    async def choose_from_list(items: list[Any]) -> Any:
        return Random().choice(items)

    @staticmethod
    async def session_commit(
        session: AsyncSession,
    ) -> None:
        await session.commit()

    @staticmethod
    async def read_books(*, session: AsyncSession) -> list[Book]:
        stmt = select(Book)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def clean_db(*, session: AsyncSession) -> tuple[int, int]:
        books_deleted = (await session.scalar(select(func.count()).select_from(Book))) or 0
        authors_deleted = (await session.scalar(select(func.count()).select_from(Author))) or 0
        await session.execute(delete(M2MBooksAuthors))
        await session.execute(delete(Book))
        await session.execute(delete(Author))
        await session.flush()
        return authors_deleted, books_deleted

    async def make_payment(self, seconds: int | None = None) -> None:
        """Симулирует сетевой запрос"""
        delay = seconds
        if delay is None:
            delay = await self.choose_from_list(self.app_settings.PAYMENTS_PROCESS_IN_SECONDS)
        await sleep(delay=delay)

        if Random().random() < self.app_settings.PAYMENT_FAILURE_RATE:
            msg = "Payment service is unavailable"
            raise PaymentError(msg)

    async def worker(
        self,
    ) -> list[Book]:
        async with transaction() as session:
            books = await self.read_books(session=session)
            await self.call_billing()
            return books

    async def update_books_status(self, *, session: AsyncSession, books: list[Book]) -> None:
        available_statuses = list(BookStatus)
        for book in books:
            book.status = await self.choose_from_list(available_statuses)
        await session.flush()

    async def call_billing(self) -> None:
        try:
            await self.make_payment()
        except PaymentError as err:
            raise HTTPException(
                status_code=400,
                detail="Payment service is unavailable",
            ) from err

    async def sync_books(self, *, session: AsyncSession, books: list[Book]) -> None:
        try:
            await self.make_payment()
        except PaymentError as err:
            raise HTTPException(
                status_code=400,
                detail="Payment service is unavailable",
            ) from err
        await self.update_books_status(session=session, books=books)
        await self.session_commit(session=session)

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

        await session.flush()
        return created_authors, created_books


async def get_controller() -> AsyncIterator[ClientCallController]:
    yield ClientCallController(app_settings=get_settings(AppSettings))


ConnectionControllerDep = Annotated[ClientCallController, Depends(get_controller)]
