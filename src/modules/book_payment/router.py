from fastapi import APIRouter

from src.modules.book_payment.routers.in_session import (
    no_tr_router as in_session_no_tr_router,
    tr_router as in_session_tr_router,
)
from src.modules.book_payment.routers.seed import router as seed_router

router = APIRouter(prefix="/book-payments", tags=["payment"])
router.include_router(seed_router)
router.include_router(in_session_tr_router)
router.include_router(in_session_no_tr_router)
