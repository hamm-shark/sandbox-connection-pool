from asyncio import gather
from typing import Any

from fastapi import APIRouter

from src.modules.book_payment.controllers.out_session import BookPaymentOutSessionControllerDep
from src.modules.book_payment.schemas import BookResponse, ClintCallSession

no_tr_router = APIRouter(
    prefix="/out-session/no-transaction",
    tags=["payment: out-session/no-transaction"],
)

tr_router = APIRouter(
    prefix="/out-session/transaction",
    tags=["payment: out-session/transaction"],
)


@no_tr_router.get("/")
async def get_books(controller: BookPaymentOutSessionControllerDep) -> list[BookResponse]:
    return await controller.get_books()


@no_tr_router.post("/sequential")
async def get_books_sequential(
    body: ClintCallSession, controller: BookPaymentOutSessionControllerDep
) -> list[BookResponse]:
    session_nums = await controller.get_session_nums(body.session_nums)
    books = []
    for _ in range(session_nums):
        books = await controller.get_books()
    return books


@no_tr_router.post("/parallel")
async def get_books_parallel(body: ClintCallSession, controller: BookPaymentOutSessionControllerDep) -> dict[str, Any]:
    session_nums = await controller.get_session_nums(body.session_nums)

    result = await gather(
        *(controller.get_books() for _ in range(session_nums)),
        return_exceptions=True,
    )

    return {
        "success": sum(not isinstance(item, Exception) for item in result),
        "failed": sum(isinstance(item, Exception) for item in result),
        "results": [str(item) if isinstance(item, Exception) else "ok" for item in result],
    }


@tr_router.get("/transaction")
async def update_book(controller: BookPaymentOutSessionControllerDep) -> list[BookResponse]:
    return await controller.update_books()


@tr_router.post("/sequential")
async def update_books_sequential(
    body: ClintCallSession, controller: BookPaymentOutSessionControllerDep
) -> list[BookResponse]:
    session_nums = await controller.get_session_nums(body.session_nums)
    books = []
    for _ in range(session_nums):
        books = await controller.update_books()
    return books


@tr_router.post("/parallel")
async def update_books_parallel(
    body: ClintCallSession, controller: BookPaymentOutSessionControllerDep
) -> dict[str, Any]:
    session_nums = await controller.get_session_nums(body.session_nums)

    result = await gather(
        *(controller.update_books() for _ in range(session_nums)),
        return_exceptions=True,
    )

    return {
        "success": sum(not isinstance(item, Exception) for item in result),
        "failed": sum(isinstance(item, Exception) for item in result),
        "results": [str(item) if isinstance(item, Exception) else "ok" for item in result],
    }
