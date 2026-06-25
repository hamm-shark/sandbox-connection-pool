import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from random import SystemRandom as Random
from typing import Any, cast
from uuid import UUID

from faker import Faker
from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.infra.postgres.models import Author, Book
from src.infra.postgres.transaction_manager import TransactionManager
from src.main.app_config import AppSettings
from src.main.enums import BookStatus
from src.modules.book_payment.exceptions import ClientCallError, DomesticServiceError, PaymentError

logger = logging.getLogger("app")


@dataclass(slots=True)
class BaseController:
    tr_manager: TransactionManager


class BookPaymentBaseController:
    def __init__(self, app_settings: AppSettings) -> None:
        self.app_settings = app_settings
        self.faker = Faker()

    @staticmethod
    def choose_from_list(items: Sequence[Any]) -> Any:
        return Random().choice(items)

    @staticmethod
    def get_random_value() -> float | int:
        return Random().random()

    @staticmethod
    async def session_flush(session: AsyncSession) -> None:
        await session.flush()

    @staticmethod
    async def session_commit(session: AsyncSession) -> None:
        await session.commit()

    @staticmethod
    async def read_book_by_ids(*, session: AsyncSession, book_ids: list[UUID]) -> list[Book]:
        stmt = select(Book).options(selectinload(Book.authors)).where(Book.id.in_(book_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    def get_successful_status(self) -> BookStatus:
        return self.choose_from_list(BookStatus.successful())

    def get_failed_status(self) -> BookStatus:
        return self.choose_from_list(BookStatus.failed())

    async def read_books(self, *, session: AsyncSession, limit: int) -> list[Book]:
        status_group = self.choose_from_list([BookStatus.failed(), BookStatus.successful(), (BookStatus.ARCHIVED,)])
        stmt = select(Book).options(selectinload(Book.authors)).where(Book.status.in_(status_group)).limit(limit)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_session_nums(self, session_nums: int | None) -> int:
        if session_nums is None:
            session_nums = self.choose_from_list(self.app_settings.SESSION_NUMBERS)
        return session_nums

    async def process_nothing(self, duration: float | None) -> None:
        delay = duration
        if delay is None:
            delay = self.choose_from_list(self.app_settings.DEFAULT_PROCESS_DELAYS)
        await asyncio.sleep(delay=delay)

    async def do_payment(self, duration: float | None = None) -> None:
        """Симулирует сетевой запрос"""
        exc_type = PaymentError
        failure_rate = self.app_settings.PAYMENT_FAILURE_RATE
        await self.do_work(duration, failure_rate, exc_type)

    async def do_household_chores(self, duration: float | None = None) -> None:
        """Симулирует работу внутреннего сервиса"""
        exc_type = DomesticServiceError
        failure_rate = self.app_settings.DOMESTIC_FAILURE_RATE
        await self.do_work(duration, failure_rate, exc_type)

    def raise_failure(self, failure_rate: float, exc_type: type[ClientCallError]) -> None:
        failure_value = self.get_random_value()
        if failure_value < failure_rate:
            raise exc_type()

    async def do_work(self, duration: float | None, failure_rate: float, exc_type: type[ClientCallError]) -> None:
        await self.process_nothing(duration=duration)
        self.raise_failure(failure_rate, exc_type)

    async def call_billing(self) -> None:
        try:
            process_delay = self.choose_from_list(self.app_settings.PAYMENT_DELAYS)
            await self.do_payment(duration=process_delay)
        except PaymentError as err:
            raise HTTPException(
                status_code=400,
                detail=err.message,
            ) from err

    async def call_domestic_service(self) -> None:
        try:
            process_delay = self.choose_from_list(self.app_settings.DOMESTIC_DELAYS)
            await self.do_household_chores(duration=process_delay)
        except DomesticServiceError as err:
            raise HTTPException(
                status_code=400,
                detail=err.message,
            ) from err

    def set_book_status(self, book_status: BookStatus) -> BookStatus:
        new_status = BookStatus.CREATED
        if book_status in BookStatus.successful():
            new_status = self.get_failed_status()
        elif book_status in BookStatus.failed() or book_status == BookStatus.ARCHIVED:
            new_status = self.get_successful_status()
        archiving_chance = self.get_random_value()
        if archiving_chance < self.app_settings.ARCHIVED_STATUS_RATE:
            new_status = BookStatus.ARCHIVED
        return new_status

    async def set_author_name(self, author: Author) -> None:
        author_name = self.choose_from_list(
            [self.faker.name_male(), self.faker.name_female(), self.faker.name_nonbinary()]
        )
        author.name = author_name

    async def update_books_status(self, *, session: AsyncSession, books: list[Book]) -> list[UUID]:
        books_to_update = []
        updated_books_ids = []
        for book in books:
            new_status = self.set_book_status(book.status)
            books_to_update.append({"id": book.id, "status": new_status})
            updated_books_ids.append(book.id)

        # Acquire row locks in deterministic order to avoid lock-order inversion across concurrent requests.
        ordered_ids = sorted(updated_books_ids)
        await session.execute(select(Book.id).where(Book.id.in_(ordered_ids)).order_by(Book.id).with_for_update())

        # Keep UPDATE order deterministic as well.
        ordered_updates = sorted(
            books_to_update,
            key=lambda item: cast("UUID", item["id"]),
        )
        await session.execute(update(Book), ordered_updates)
        return updated_books_ids
