import asyncio
from dataclasses import dataclass
from random import SystemRandom as Random
from typing import Any

from faker import Faker
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.infra.postgres.models import Book
from src.infra.postgres.transaction_manager import TransactionManager
from src.main.app_config import AppSettings
from src.main.enums import BookStatus
from src.modules.book_payment.exceptions import ClientCallError, DomesticServiceError, PaymentError


@dataclass(slots=True)
class BaseController:
    tr_manager: TransactionManager


class BookPaymentBaseController:
    def __init__(self, app_settings: AppSettings) -> None:
        self.app_settings = app_settings
        self.faker = Faker()

    @staticmethod
    async def choose_from_list(items: list[Any]) -> Any:
        return Random().choice(items)

    @staticmethod
    async def get_random_value() -> float | int:
        return Random().random()

    @staticmethod
    async def session_flush(session: AsyncSession) -> None:
        await session.flush()

    @staticmethod
    async def session_commit(session: AsyncSession) -> None:
        await session.commit()

    @staticmethod
    async def read_books(*, session: AsyncSession) -> list[Book]:
        stmt = select(Book).options(joinedload(Book.authors))
        result = await session.execute(stmt)
        return list(result.scalars().unique().all())

    async def get_session_nums(self, session_nums: int | None) -> int:
        if session_nums is None:
            session_nums = await self.choose_from_list(self.app_settings.SESSION_NUMBERS)
        return session_nums

    async def process_nothing(self, duration: float | None) -> None:
        delay = duration
        if delay is None:
            delay = await self.choose_from_list(self.app_settings.DEFAULT_PROCESS_DELAYS)
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

    async def raise_failure(self, failure_rate: float, exc_type: type[ClientCallError]) -> None:
        failure_value = await self.get_random_value()
        if failure_value < failure_rate:
            raise exc_type()

    async def do_work(self, duration: float | None, failure_rate: float, exc_type: type[ClientCallError]) -> None:
        await self.process_nothing(duration=duration)
        await self.raise_failure(failure_rate, exc_type)

    async def call_billing(self) -> None:
        try:
            process_delay = await self.choose_from_list(self.app_settings.PAYMENT_DELAYS)
            await self.do_payment(duration=process_delay)
        except PaymentError as err:
            raise HTTPException(
                status_code=400,
                detail=err.message,
            ) from err

    async def call_domestic_service(self) -> None:
        try:
            process_delay = await self.choose_from_list(self.app_settings.DOMESTIC_DELAYS)
            await self.do_household_chores(duration=process_delay)
        except DomesticServiceError as err:
            raise HTTPException(
                status_code=400,
                detail=err.message,
            ) from err

    async def update_books_status(self, *, session: AsyncSession, books: list[Book]) -> None:
        available_statuses = list(BookStatus)
        for book in books:
            book.status = await self.choose_from_list(available_statuses)
        await self.session_flush(session)
