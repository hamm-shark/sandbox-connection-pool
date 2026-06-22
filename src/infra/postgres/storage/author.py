from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from src.infra.postgres.models import Author
from src.infra.postgres.storage.base_storage import PostgresStorage
from src.modules.authors.schemas import AuthorResponse


class AuthorStorage(PostgresStorage[Author]):
    async def create(self, name: str) -> Author:
        stmt = insert(Author).values(name=name).returning(Author)
        result = await self._db.execute(stmt)
        return result.scalar_one()

    async def read_authors(self) -> list[AuthorResponse]:
        result = await self._db.execute(select(Author))
        return [AuthorResponse.model_validate(el) for el in result.scalars().all()]
