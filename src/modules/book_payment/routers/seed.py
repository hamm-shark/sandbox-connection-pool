from fastapi import APIRouter

from src.infra.postgres.pg import transaction
from src.modules.book_payment.controllers.seed import BookPaymentSeedControllerDep
from src.modules.book_payment.schemas import CleanDbResponse, SeedBooksRequest, SeedBooksResponse

router = APIRouter(prefix="/seed", tags=["payment"])


@router.post("/")
async def seed_authors_with_books(
    body: SeedBooksRequest,
    controller: BookPaymentSeedControllerDep,
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


@router.delete("/")
async def clean_seeded_data(controller: BookPaymentSeedControllerDep) -> CleanDbResponse:
    async with transaction() as session:
        authors_deleted, books_deleted = await controller.clean_db(session=session)
        await controller.session_commit(session=session)
        return CleanDbResponse(
            authors_deleted=authors_deleted,
            books_deleted=books_deleted,
        )
