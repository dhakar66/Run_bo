from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.challenge import Challenge, ChallengeStatus
from schemas.challenge import ChallengeCreate


async def create_challenge(
    session: AsyncSession, challenge_data: ChallengeCreate
) -> Challenge:
    challenge = Challenge(**challenge_data.model_dump())
    session.add(challenge)
    await session.commit()
    await session.refresh(challenge)
    return challenge


async def list_challenges(
    session: AsyncSession,
    *,
    status: ChallengeStatus | None = None,
    offset: int = 0,
    limit: int = 50,
) -> list[Challenge]:
    statement = select(Challenge)
    if status is not None:
        statement = statement.where(Challenge.status == status)
    statement = statement.order_by(Challenge.starts_at.asc()).offset(offset).limit(limit)
    result = await session.scalars(statement)
    return list(result.all())


async def get_challenge(session: AsyncSession, challenge_id: UUID) -> Challenge | None:
    return await session.get(Challenge, challenge_id)
