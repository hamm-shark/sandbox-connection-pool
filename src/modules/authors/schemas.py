from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuthorBase(BaseModel):
    name: str


class AuthorCreateRequest(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
