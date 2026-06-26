from asyncio import gather
from typing import Any

from fastapi import APIRouter

from src.infra.postgres.pg import transaction
from src.modules.book_payment.controllers.in_session import BookPaymentInSessionControllerDep
from src.modules.book_payment.schemas import BookResponse, ClintCallRequest

no_tr_router = APIRouter(
    prefix="/in-session/no-transaction",
    tags=["payment: in-session/no-transaction"],
)

tr_router = APIRouter(
    prefix="/in-session/transaction",
    tags=["payment: in-session/transaction"],
)


@no_tr_router.get("/")
async def get_books(controller: BookPaymentInSessionControllerDep, limit: int = 50) -> list[BookResponse]:
    async with transaction() as session:
        return await controller.get_books(session=session, limit=limit)


@no_tr_router.post("/sequential")
async def get_books_sequential(
    body: ClintCallRequest, controller: BookPaymentInSessionControllerDep
) -> list[BookResponse]:
    session_nums = await controller.get_session_nums(body.session_nums)

    for _ in range(session_nums):
        async with transaction() as session:
            books = await controller.get_books(session=session, limit=body.limit)
    return books


@no_tr_router.post("/parallel")
async def get_books_parallel(body: ClintCallRequest, controller: BookPaymentInSessionControllerDep) -> dict[str, Any]:
    session_nums = await controller.get_session_nums(body.session_nums)

    result = await gather(
        *(controller.worker(body.limit) for _ in range(session_nums)),
        return_exceptions=True,
    )

    return {
        "success": sum(not isinstance(item, Exception) for item in result),
        "failed": sum(isinstance(item, Exception) for item in result),
    }


@tr_router.get("/")
async def update_book(controller: BookPaymentInSessionControllerDep, limit: int = 50) -> list[BookResponse]:
    async with transaction() as session:
        return await controller.update_books(session=session, limit=limit)


@tr_router.post("/sequential")
async def update_books_sequential(
    body: ClintCallRequest, controller: BookPaymentInSessionControllerDep
) -> list[BookResponse]:
    session_nums = await controller.get_session_nums(body.session_nums)

    for _ in range(session_nums):
        async with transaction() as session:
            books = await controller.update_books(session=session, limit=body.limit)
    return books


@tr_router.post("/parallel")
async def update_books_parallel(
    body: ClintCallRequest, controller: BookPaymentInSessionControllerDep
) -> dict[str, Any]:
    session_nums = await controller.get_session_nums(body.session_nums)

    result = await gather(
        *(controller.worker_for_update(body.limit) for _ in range(session_nums)),
        return_exceptions=True,
    )

    return {
        "success": sum(not isinstance(item, Exception) for item in result),
        "failed": sum(isinstance(item, Exception) for item in result),
    }
