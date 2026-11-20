from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api import api_router
from core.config import get_settings
from core.request_logging import log_request

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    swagger_ui_oauth2_redirect_url=None,
    description=(
        "API for managing Run Tib virtual challenges and, in later phases, "
        "participant progress imported from Strava."
    ),
    openapi_tags=[
        {
            "name": "Challenges",
            "description": "Create and browse time-bound 50 km / 100 km challenges.",
        }
    ],
)

app.middleware("http")(log_request)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health", tags=["System"], summary="Check API health")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}
