from uuid import UUID

from pydantic import BaseModel


class AuthorBase(BaseModel):
    name: str


class AuthorCreateRequest(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    id: UUID
