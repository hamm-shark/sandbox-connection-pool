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

no_tr_router = APIRouter(
    prefix="/in-session/no-transaction",
    tags=["client-call: in-session/no-transaction"],
)

tr_router = APIRouter(
    prefix="/in-session/transaction",
    tags=["client-call: in-session/transaction"],
)


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


@no_tr_router.get("/")
async def get_books(controller: ConnectionControllerDep) -> list[BookResponse]:
    async with transaction() as session:
        books = await controller.get_books(session=session)
        return [BookResponse.model_validate(book) for book in books]


@no_tr_router.post("/sequential")
async def get_books_sequential(body: ClintCallSession, controller: ConnectionControllerDep) -> list[BookResponse]:
    session_nums = await controller.get_session_nums(body.session_nums)

    for _ in range(session_nums):
        async with transaction() as session:
            books = await controller.get_books(session=session)
    return [BookResponse.model_validate(book) for book in books]


@no_tr_router.post("/parallel")
async def get_books_parallel(body: ClintCallSession, controller: ConnectionControllerDep) -> dict[str, Any]:
    session_nums = await controller.get_session_nums(body.session_nums)

    result = await gather(
        *(controller.worker() for _ in range(session_nums)),
        return_exceptions=True,
    )

    return {
        "success": sum(not isinstance(item, Exception) for item in result),
        "failed": sum(isinstance(item, Exception) for item in result),
        "results": [str(item) if isinstance(item, Exception) else "ok" for item in result],
    }


@tr_router.get("/in-session/transaction")
async def update_book(controller: ConnectionControllerDep) -> list[BookResponse]:
    async with transaction() as session:
        books = await controller.get_books(session=session)
        return [BookResponse.model_validate(book) for book in books]


@tr_router.post("/in-session/sequential/transaction")
async def update_books_sequential(body: ClintCallSession, controller: ConnectionControllerDep) -> list[BookResponse]:
    session_nums = await controller.get_session_nums(body.session_nums)

    for _ in range(session_nums):
        async with transaction() as session:
            books = await controller.get_books(session=session)
    return [BookResponse.model_validate(book) for book in books]


@tr_router.post("/in-session/parallel/transaction")
async def update_books_parallel(body: ClintCallSession, controller: ConnectionControllerDep) -> dict[str, Any]:
    session_nums = await controller.get_session_nums(body.session_nums)

    result = await gather(
        *(controller.worker_for_update() for _ in range(session_nums)),
        return_exceptions=True,
    )

    return {
        "success": sum(not isinstance(item, Exception) for item in result),
        "failed": sum(isinstance(item, Exception) for item in result),
        "results": [str(item) if isinstance(item, Exception) else "ok" for item in result],
    }
