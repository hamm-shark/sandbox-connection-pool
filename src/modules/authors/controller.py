from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends

from src.infra.postgres.transaction_manager import PostgresTrManagerDep
from src.modules.authors.schemas import AuthorCreateRequest, AuthorResponse
from src.modules.base.controller import BaseController


class AuthorController(BaseController):
    async def read_authors(self) -> list[AuthorResponse]:
        async with self.tr_manager as mng:
            return await mng.author.read_authors()

    async def create_author(self, data: AuthorCreateRequest) -> AuthorResponse:
        async with self.tr_manager as mng:
            author = await mng.author.create(data.name)
        return AuthorResponse.model_validate(author)


async def get_controller(tr_manager: PostgresTrManagerDep) -> AsyncIterator[AuthorController]:
    yield AuthorController(tr_manager=tr_manager)


AuthorControllerDep = Annotated[AuthorController, Depends(get_controller)]
