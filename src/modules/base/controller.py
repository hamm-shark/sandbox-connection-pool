from asyncio import sleep
from dataclasses import dataclass
from random import SystemRandom as Random
from typing import Any

from faker import Faker
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infra.postgres.models import Book
from src.infra.postgres.transaction_manager import TransactionManager
from src.main.app_config import AppSettings
from src.main.enums import BookStatus


@dataclass(slots=True)
class BaseController:
    tr_manager: TransactionManager


class ClientCallError(Exception):
    message = "Client call failed"

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)


class PaymentError(ClientCallError):
    """Имитация ошибки платежного сервиса."""

    message: str = "Payment service is unavailable"


class DomesticServiceError(ClientCallError):
    """Имитация ошибки работы сервиса."""

    message: str = "Domestic service is unavailable"


class BookPaymentBaseController:
    def __init__(self, app_settings: AppSettings) -> None:
        self.app_settings = app_settings
        self.faker = Faker()

    @staticmethod
    async def choose_from_list(items: list[Any]) -> Any:
        return Random().choice(items)

    @staticmethod
    async def session_flush(session: AsyncSession) -> None:
        await session.flush()

    @staticmethod
    async def session_commit(session: AsyncSession) -> None:
        await session.commit()

    @staticmethod
    async def read_books(*, session: AsyncSession) -> list[Book]:
        stmt = select(Book)
        result = await session.execute(stmt)
        return list(result.scalars().all())

    async def get_session_nums(self, session_nums: int | None) -> int:
        if session_nums is None:
            session_nums = await self.choose_from_list(self.app_settings.SESSION_NUMBERS)
        return session_nums

    async def process_nothing(self, seconds: int | None) -> None:
        delay = seconds
        if delay is None:
            delay = await self.choose_from_list(self.app_settings.PAYMENTS_PROCESS_IN_SECONDS)
        await sleep(delay=delay)

    async def do_payment(self, seconds: int | None = None) -> None:
        """Симулирует сетевой запрос"""
        exc_type = PaymentError
        failure_rate = self.app_settings.PAYMENT_FAILURE_RATE
        await self.do_work(seconds, failure_rate, exc_type)

    async def do_household_chores(self, seconds: int | None = None) -> None:
        """Симулирует работу внутреннего сервиса"""
        exc_type = DomesticServiceError
        failure_rate = self.app_settings.DOMESTIC_FAILURE_RATE
        await self.do_work(seconds, failure_rate, exc_type)

    async def do_work(self, seconds: int | None, failure_rate: float, exc_type: type[ClientCallError]) -> None:
        await self.process_nothing(seconds=seconds)
        if Random().random() < failure_rate:
            raise exc_type()

    async def call_billing(self) -> None:
        try:
            await self.do_payment()
        except PaymentError as err:
            raise HTTPException(
                status_code=400,
                detail=err.message,
            ) from err

    async def call_domestic_service(self) -> None:
        try:
            await self.do_household_chores()
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
