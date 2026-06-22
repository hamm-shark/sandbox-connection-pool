from uuid import UUID

from sqlalchemy import select

from src.infra.postgres.models.book import Book
from src.infra.postgres.storage.base_storage import PostgresStorage
from src.main.enums import BookStatus
from src.modules.books.schemas import BookResponse


class BookStorage(PostgresStorage[Book]):
    async def get_by_id(self, book_id: UUID) -> Book | None:
        result = await self._db.execute(select(Book).where(Book.id == book_id))
        return result.scalar_one_or_none()

    async def read_books(self) -> list[BookResponse]:
        result = await self._db.execute(select(Book))
        return [BookResponse.model_validate(el) for el in result.scalars().all()]

    async def create(self, book_id: Book) -> Book:
        self._db.add(book_id)
        await self._db.flush()
        await self._db.refresh(book_id)
        return book_id

    async def update_status(
        self,
        book_id: UUID,
        status: BookStatus,
    ) -> Book | None:
        book = await self.get_by_id(book_id)
        if book is None:
            return None
        book.status = status
        await self._db.flush()
        return book
