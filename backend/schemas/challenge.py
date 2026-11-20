from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.challenge import ChallengeStatus


class ChallengeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str | None = None
    starts_at: datetime
    ends_at: datetime
    status: ChallengeStatus = ChallengeStatus.DRAFT

    @model_validator(mode="after")
    def validate_date_range(self) -> "ChallengeCreate":
        if self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be later than starts_at")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "name": "Run Tib Autumn Challenge",
                    "description": "Complete 50 km or 100 km during the challenge window.",
                    "starts_at": "2026-10-01T00:00:00Z",
                    "ends_at": "2026-10-31T23:59:59Z",
                    "status": "published",
                }
            ]
        }
    )


class ChallengeRead(BaseModel):
    id: UUID
    name: str
    description: str | None
    starts_at: datetime
    ends_at: datetime
    status: ChallengeStatus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
