from asyncio import gather
from typing import Any

from fastapi import APIRouter

from src.infra.postgres.models import Book
from src.infra.postgres.pg import transaction
from src.modules.client_calls.controller import ConnectionControllerDep
from src.modules.client_calls.schemas import ClintCallSession

router = APIRouter(prefix="/client-call", tags=["client-call"])


@router.get("/in-session/no-transaction")
async def get_book_no_transaction(controller: ConnectionControllerDep) -> list[Book]:
    async with transaction() as session:
        books = await controller.read_books(session=session)
        await controller.call_billing()
        return books


@router.post("/in-session/sequential/no-transaction")
async def get_book_sequential_no_transaction(body: ClintCallSession, controller: ConnectionControllerDep) -> list[Book]:
    session_nums = body.session_nums
    if session_nums is None:
        session_nums = await controller.choose_from_list(controller.app_settings.SESSION_NUMBERS)

    for _ in range(session_nums):
        async with transaction() as session:
            books = await controller.read_books(session=session)
            await controller.call_billing()
    return books


@router.post("/in-session/parallel/no-transaction")
async def get_book_parallel_no_transaction(
    body: ClintCallSession, controller: ConnectionControllerDep
) -> dict[str, Any]:
    session_nums = body.session_nums

    if session_nums is None:
        session_nums = await controller.choose_from_list(controller.app_settings.SESSION_NUMBERS)

    result = await gather(
        *(controller.worker() for _ in range(session_nums)),
        return_exceptions=True,
    )

    return {
        "success": sum(not isinstance(item, Exception) for item in result),
        "failed": sum(isinstance(item, Exception) for item in result),
        "results": [str(item) if isinstance(item, Exception) else "ok" for item in result],
    }
