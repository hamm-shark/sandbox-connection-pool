from uuid import UUID

from pydantic import BaseModel, field_validator


class BookBase(BaseModel):
    title: str
    authors: list[UUID]
    genre: str


class BookCreateRequest(BookBase):
    @field_validator("authors", mode="before")
    @classmethod
    def validate_authors(cls, value: list[UUID]) -> list[UUID]:
        if len(value) != len(set(value)):
            msg = "authors must have unique ids"
            raise ValueError(msg)
        return value


class BookResponse(BookBase):
    id: UUID
