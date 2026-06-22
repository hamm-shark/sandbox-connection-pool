from fastapi import APIRouter

from src.modules.authors.router import router as authors_router
from src.modules.books.router import router as books_router
from src.modules.utils.router import router as utils_router

router = APIRouter(prefix="/api")
router.include_router(
    utils_router,
)
router.include_router(
    books_router,
)
router.include_router(authors_router)
