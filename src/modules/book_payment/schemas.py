from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ClintCallSession(BaseModel):
    session_nums: int | None = None


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str


class SeedBooksRequest(BaseModel):
    authors_count: int = 3
    books_per_author: int = 2


class SeedBooksResponse(BaseModel):
    authors_created: int
    books_created: int


class CleanDbResponse(BaseModel):
    authors_deleted: int
    books_deleted: int
