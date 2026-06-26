import asyncio
import logging
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from random import SystemRandom as Random
from typing import Any
from uuid import UUID

from faker import Faker
from fastapi import HTTPException
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.postgres.models import Book
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
        stmt = select(Book).where(Book.id.in_(book_ids))
        result = await session.execute(stmt)
        return list(result.scalars().all())

    def get_successful_status(self) -> BookStatus:
        return self.choose_from_list(BookStatus.successful())

    def get_failed_status(self) -> BookStatus:
        return self.choose_from_list(BookStatus.failed())

    async def read_books(self, *, session: AsyncSession, limit: int) -> list[Book]:
        status_group = self.choose_from_list([BookStatus.failed(), BookStatus.successful()])
        stmt = (
            select(Book)
            .where(Book.status.in_(status_group))
            .order_by(Book.id)
            .with_for_update(skip_locked=True)
            .limit(limit)
        )
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
        elif book_status in BookStatus.failed():
            new_status = self.get_successful_status()
        return new_status

    async def update_books_status(
        self,
        *,
        session: AsyncSession,
        books: list[Book],
    ) -> list[UUID]:
        if not books:
            return []

        dt_updated_at = datetime.now(UTC)

        values: list[str] = []
        params: dict[str, UUID | str | datetime] = {}
        updated_books_ids = []

        for i, book in enumerate(sorted(books, key=lambda b: b.id)):
            values.append(f"(:id_{i}, :status_{i}, :updated_at_{i})")

            params[f"id_{i}"] = book.id
            params[f"status_{i}"] = self.set_book_status(book.status).value
            params[f"updated_at_{i}"] = dt_updated_at

            updated_books_ids.append(book.id)

        stmt = text(f"""
            UPDATE books AS b
            SET
                status = v.status::book_status,
                updated_at = v.updated_at
            FROM (
                VALUES
                    {", ".join(values)}
            ) AS v(id, status, updated_at)
            WHERE b.id = v.id::uuid
        """)
        await session.execute(stmt, params)
        return updated_books_ids
