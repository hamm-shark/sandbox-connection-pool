from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuthorBase(BaseModel):
    name: str
    model_config = ConfigDict(from_attributes=True)


class AuthorCreateRequest(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    id: UUID
