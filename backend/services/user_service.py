from typing import Any
import logging

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import get_settings
from models.user import User

logger = logging.getLogger("uvicorn.error.auth")


def profile_string(profile: dict[str, Any], field: str, limit: int) -> str | None:
    value = profile.get(field)
    return value[:limit] if isinstance(value, str) else None


async def get_or_create_user(session: AsyncSession, subject: str, access_token: str) -> User:
    user = await session.scalar(select(User).where(User.auth0_subject == subject))
    if user is None:
        logger.info("auth.user_provisioning: loading verified profile for a new account")
        # Access tokens need not contain profile claims. Fetch them from Auth0,
        # never from an unverified profile supplied by the browser.
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"https://{get_settings().auth0_domain}/userinfo",
                    headers={"Authorization": f"Bearer {access_token}"},
                )
            response.raise_for_status()
            profile = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            status_code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else "unavailable"
            logger.error("auth.profile_failed: %s status=%s; check Auth0 connectivity and openid/profile/email scopes", type(exc).__name__, status_code)
            raise HTTPException(503, "Unable to load your sign-in profile. Please try again.") from exc
        if not isinstance(profile, dict) or profile.get("sub") != subject:
            logger.warning("auth.profile_mismatch: profile does not match the verified token subject")
            raise HTTPException(401, "Sign-in profile does not match the access token")
        await session.execute(
            insert(User).values(
                auth0_subject=subject,
                email=profile_string(profile, "email", 320),
                display_name=profile_string(profile, "name", 150),
                avatar_url=profile_string(profile, "picture", 2048),
            ).on_conflict_do_nothing(index_elements=[User.auth0_subject])
        )
        await session.commit()
        logger.info("auth.user_saved: account committed to users table")
        user = await session.scalar(select(User).where(User.auth0_subject == subject))
    if user is None:
        raise HTTPException(503, "Unable to create your account. Please try again.")
    if not user.is_active:
        logger.warning("auth.account_disabled: refusing access")
        raise HTTPException(403, "Your account is disabled")
    return user
