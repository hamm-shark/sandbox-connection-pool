from fastapi import APIRouter

from src.modules.authors.controller import AuthorControllerDep
from src.modules.authors.schemas import AuthorCreateRequest, AuthorResponse

router = APIRouter(prefix="/authors", tags=["authors"])


@router.get("/")
async def get(controller: AuthorControllerDep) -> list[AuthorResponse]:
    return await controller.read_authors()


@router.post("/")
async def post(body: AuthorCreateRequest, controller: AuthorControllerDep) -> AuthorResponse:
    return await controller.create_author(body)
