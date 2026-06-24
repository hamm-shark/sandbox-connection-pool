import asyncio

from fastapi import APIRouter
from sqlalchemy import select

from src.infra.postgres.models import Book
from src.infra.postgres.pg import transaction

router = APIRouter(prefix="/utils", tags=["utils"])


@router.get("/health-check/")
async def health_check() -> bool:
    return True


@router.get("/health-check/test-db")
async def health_check_test_db() -> dict[str, bool]:
    async with transaction() as session:
        await session.execute(select(Book).limit(1))
        await asyncio.sleep(0.2)
    return {"ok": True}
