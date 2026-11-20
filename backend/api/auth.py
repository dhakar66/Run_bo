from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from core.auth import ClaimsDependency, bearer
from core.database import get_db_session
from models.user import User
from services.user_service import get_or_create_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None
    is_active: bool


async def get_current_user(
    claims: ClaimsDependency,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> User:
    return await get_or_create_user(session, claims["sub"], credentials.credentials)


CurrentUser = Annotated[User, Depends(get_current_user)]


async def require_challenge_creator(claims: ClaimsDependency, user: CurrentUser) -> User:
    permissions = claims.get("permissions", [])
    if not isinstance(permissions, list) or "create:challenges" not in permissions:
        raise HTTPException(403, "The create:challenges permission is required")
    return user


@router.get("/me", response_model=UserRead, summary="Get or create your Run Tib account")
async def me(user: CurrentUser) -> User:
    return user
