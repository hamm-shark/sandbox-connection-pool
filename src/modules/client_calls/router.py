from asyncio import gather
from typing import Any

from fastapi import APIRouter

from src.infra.postgres.pg import transaction
from src.modules.client_calls.controller import ConnectionControllerDep
from src.modules.client_calls.schemas import (
    BookResponse,
    CleanDbResponse,
    ClintCallSession,
    SeedBooksRequest,
    SeedBooksResponse,
)

router = APIRouter(prefix="/client-call", tags=["client-call"])


@router.get("/in-session/no-transaction")
async def get_book_no_transaction(controller: ConnectionControllerDep) -> list[BookResponse]:
    async with transaction() as session:
        books = await controller.read_books(session=session)
        await controller.call_billing()
        return [BookResponse.model_validate(book) for book in books]


@router.post("/in-session/sequential/no-transaction")
async def get_book_sequential_no_transaction(
    body: ClintCallSession, controller: ConnectionControllerDep
) -> list[BookResponse]:
    session_nums = body.session_nums
    if session_nums is None:
        session_nums = await controller.choose_from_list(controller.app_settings.SESSION_NUMBERS)

    for _ in range(session_nums):
        async with transaction() as session:
            books = await controller.read_books(session=session)
            await controller.call_billing()
    return [BookResponse.model_validate(book) for book in books]


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


@router.post("/seed")
async def seed_authors_with_books(
    body: SeedBooksRequest,
    controller: ConnectionControllerDep,
) -> SeedBooksResponse:
    async with transaction() as session:
        authors_created, books_created = await controller.seed_authors_with_books(
            session=session,
            authors_count=body.authors_count,
            books_per_author=body.books_per_author,
        )
        await controller.session_commit(session=session)
        return SeedBooksResponse(
            authors_created=authors_created,
            books_created=books_created,
        )


@router.delete("/seed")
async def clean_seeded_data(controller: ConnectionControllerDep) -> CleanDbResponse:
    async with transaction() as session:
        authors_deleted, books_deleted = await controller.clean_db(session=session)
        await controller.session_commit(session=session)
        return CleanDbResponse(
            authors_deleted=authors_deleted,
            books_deleted=books_deleted,
        )
