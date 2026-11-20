import logging
import time
import traceback
from uuid import uuid4

from fastapi import Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("uvicorn.error.api")


async def log_request(request: Request, call_next):
    request_id = uuid4().hex[:12]
    started = time.monotonic()
    try:
        response = await call_next(request)
    except Exception as exc:
        # Exception strings can contain SQL parameter values or credentials.
        # Log types, SQLSTATE, and code locations without request bodies/headers.
        original = getattr(exc, "orig", exc)
        sqlstate = getattr(original, "sqlstate", None)
        database_error = isinstance(exc, SQLAlchemyError) or sqlstate is not None
        frames = " -> ".join(
            f"{frame.filename.rsplit('/', 1)[-1]}:{frame.lineno}:{frame.name}"
            for frame in traceback.extract_tb(exc.__traceback__)[-6:]
        )
        logger.error(
            "request.failed id=%s error=%s cause=%s sqlstate=%s locations=%s hint=%s",
            request_id, type(exc).__name__, type(original).__name__, sqlstate, frames,
            "Check database connectivity, credentials, and alembic upgrade head" if database_error else "Inspect the code locations above",
        )
        response = JSONResponse(
            status_code=503 if database_error else 500,
            content={"detail": "Database operation failed. Please try again." if database_error else "An unexpected server error occurred.", "request_id": request_id},
        )
    response.headers["X-Request-ID"] = request_id
    log = logger.warning if response.status_code >= 400 else logger.info
    # Exclude query strings: OAuth callback parameters must never enter these logs.
    log("request.complete id=%s method=%s path=%s status=%s duration_ms=%.1f",
        request_id, request.method, request.url.path, response.status_code,
        (time.monotonic() - started) * 1000)
    return response
