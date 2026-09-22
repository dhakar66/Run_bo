from fastapi import APIRouter

from api.challenges import router as challenges_router

api_router = APIRouter()
api_router.include_router(challenges_router)

__all__ = ["api_router"]
