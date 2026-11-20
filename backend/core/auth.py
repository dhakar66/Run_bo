from functools import lru_cache
import logging
import ssl
from typing import Annotated, Any

import certifi
import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient
from jwt.exceptions import PyJWKClientConnectionError, PyJWTError

from core.config import get_settings

bearer = HTTPBearer(auto_error=False)
logger = logging.getLogger("uvicorn.error.auth")


def unauthorized() -> HTTPException:
    return HTTPException(401, "A valid access token is required", headers={"WWW-Authenticate": "Bearer"})


@lru_cache
def jwks_client(issuer: str) -> PyJWKClient:
    return PyJWKClient(
        f"{issuer}.well-known/jwks.json", timeout=10,
        ssl_context=ssl.create_default_context(cafile=certifi.where()),
    )


def get_claims(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict[str, Any]:
    if credentials is None:
        logger.warning("auth.token_missing: send a Bearer API access token")
        raise unauthorized()
    settings = get_settings()
    if not settings.auth0_domain or not settings.auth0_audience:
        logger.error("auth.config_missing: set AUTH0_DOMAIN and AUTH0_AUDIENCE")
        raise HTTPException(503, "Authentication is not configured")
    issuer = f"https://{settings.auth0_domain}/"
    try:
        key = jwks_client(issuer).get_signing_key_from_jwt(credentials.credentials)
        claims = jwt.decode(
            credentials.credentials,
            key.key,
            algorithms=["RS256"],
            audience=settings.auth0_audience,
            issuer=issuer,
            options={"require": ["exp", "iat", "sub", "iss", "aud"]},
        )
    except PyJWKClientConnectionError as exc:
        logger.error("auth.jwks_unavailable: check HTTPS certificate trust and network (%s)", type(exc.__cause__).__name__)
        raise HTTPException(503, "Authentication service is unavailable") from exc
    except PyJWTError as exc:
        logger.warning("auth.token_rejected: %s; check token expiry, API audience, issuer, and signature", type(exc).__name__)
        raise unauthorized() from exc
    # Run Tib currently supports Google users only, not machine-to-machine tokens.
    if not isinstance(claims.get("sub"), str) or not claims["sub"].startswith("google-oauth2|"):
        logger.warning("auth.subject_rejected: expected a Google user access token")
        raise unauthorized()
    if len(claims["sub"]) > 255:
        raise unauthorized()
    return claims


ClaimsDependency = Annotated[dict[str, Any], Depends(get_claims)]
