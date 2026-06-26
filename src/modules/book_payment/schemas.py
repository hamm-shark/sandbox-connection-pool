from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.modules.authors.schemas import AuthorResponse


class ClintCallRequest(BaseModel):
    session_nums: int | None = None
    limit: int = 50


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    status: str
    authors: list[AuthorResponse]


class SeedBooksRequest(BaseModel):
    authors_count: int = 3
    books_per_author: int = 2


class SeedBooksResponse(BaseModel):
    authors_created: int
    books_created: int


class CleanDbResponse(BaseModel):
    authors_deleted: int
    books_deleted: int
