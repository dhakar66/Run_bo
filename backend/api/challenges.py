from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db_session
from models.challenge import ChallengeStatus
from schemas.challenge import ChallengeCreate, ChallengeRead
from services import challenge_service

router = APIRouter(prefix="/challenges", tags=["Challenges"])
SessionDependency = Annotated[AsyncSession, Depends(get_db_session)]


@router.post(
    "",
    response_model=ChallengeRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a challenge",
    description=(
        "Create a challenge window. Participants choose a 50 km or 100 km target "
        "when they enroll. Authentication will be added in the Auth0 phase."
    ),
)
async def create_challenge(
    challenge_data: ChallengeCreate,
    session: SessionDependency,
) -> ChallengeRead:
    return await challenge_service.create_challenge(session, challenge_data)


@router.get(
    "",
    response_model=list[ChallengeRead],
    summary="List challenges",
    description="Return challenges ordered by start date, optionally filtered by status.",
)
async def list_challenges(
    session: SessionDependency,
    challenge_status: Annotated[
        ChallengeStatus | None,
        Query(alias="status", description="Filter by challenge publication status"),
    ] = None,
    offset: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> list[ChallengeRead]:
    return await challenge_service.list_challenges(
        session, status=challenge_status, offset=offset, limit=limit
    )


@router.get(
    "/{challenge_id}",
    response_model=ChallengeRead,
    summary="Get a challenge",
    responses={404: {"description": "Challenge not found"}},
)
async def get_challenge(
    challenge_id: UUID,
    session: SessionDependency,
) -> ChallengeRead:
    challenge = await challenge_service.get_challenge(session, challenge_id)
    if challenge is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge not found",
        )
    return challenge
