from pydantic import BaseModel


class ClintCallSession(BaseModel):
    session_nums: int | None = None


class SeedBooksRequest(BaseModel):
    authors_count: int = 3
    books_per_author: int = 2


class SeedBooksResponse(BaseModel):
    authors_created: int
    books_created: int
