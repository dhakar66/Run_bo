"""Create the initial Run for Tibet schema.

Revision ID: 20260921_0001
Revises:
Create Date: 2026-09-21
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260921_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

challenge_status = postgresql.ENUM(
    "draft", "published", "cancelled", name="challenge_status", create_type=False
)
enrollment_status = postgresql.ENUM(
    "active", "completed", "withdrawn", name="enrollment_status", create_type=False
)
activity_source = postgresql.ENUM(
    "strava", "manual", name="activity_source", create_type=False
)


def upgrade() -> None:
    bind = op.get_bind()
    challenge_status.create(bind, checkfirst=True)
    enrollment_status.create(bind, checkfirst=True)
    activity_source.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("auth0_subject", sa.String(255), nullable=False),
        sa.Column("email", sa.String(320), nullable=True),
        sa.Column("display_name", sa.String(150), nullable=True),
        sa.Column("avatar_url", sa.String(2048), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("auth0_subject", name="uq_users_auth0_subject"),
    )
    op.create_index("ix_users_auth0_subject", "users", ["auth0_subject"])
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "challenges",
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", challenge_status, server_default="draft", nullable=False),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "ends_at > starts_at", name=op.f("ck_challenges_valid_date_range")
        ),
        sa.PrimaryKeyConstraint("id", name="pk_challenges"),
    )
    op.create_index("ix_challenges_starts_at", "challenges", ["starts_at"])
    op.create_index("ix_challenges_ends_at", "challenges", ["ends_at"])

    op.create_table(
        "challenge_enrollments",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("challenge_id", sa.Uuid(), nullable=False),
        sa.Column("target_distance_meters", sa.Integer(), nullable=False),
        sa.Column("status", enrollment_status, server_default="active", nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "target_distance_meters IN (50000, 100000)",
            name=op.f("ck_challenge_enrollments_valid_target_distance"),
        ),
        sa.ForeignKeyConstraint(
            ["challenge_id"],
            ["challenges.id"],
            name="fk_challenge_enrollments_challenge_id_challenges",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_challenge_enrollments_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_challenge_enrollments"),
        sa.UniqueConstraint("user_id", "challenge_id", name="uq_enrollment_user_challenge"),
    )
    op.create_index(
        "ix_challenge_enrollments_user_id", "challenge_enrollments", ["user_id"]
    )
    op.create_index(
        "ix_challenge_enrollments_challenge_id",
        "challenge_enrollments",
        ["challenge_id"],
    )

    op.create_table(
        "strava_connections",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("athlete_id", sa.BigInteger(), nullable=False),
        sa.Column("scopes", sa.String(255), nullable=False),
        sa.Column("access_token_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("refresh_token_ciphertext", sa.LargeBinary(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_strava_connections_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_strava_connections"),
        sa.UniqueConstraint("athlete_id", name="uq_strava_connections_athlete_id"),
        sa.UniqueConstraint("user_id", name="uq_strava_connections_user_id"),
    )
    op.create_index(
        "ix_strava_connections_athlete_id", "strava_connections", ["athlete_id"]
    )
    op.create_index(
        "ix_strava_connections_user_id", "strava_connections", ["user_id"]
    )

    op.create_table(
        "activities",
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("source", activity_source, nullable=False),
        sa.Column("external_activity_id", sa.String(255), nullable=True),
        sa.Column("activity_type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("distance_meters", sa.BigInteger(), nullable=False),
        sa.Column("moving_time_seconds", sa.Integer(), nullable=False),
        sa.Column("is_eligible", sa.Boolean(), server_default="true", nullable=False),
        sa.Column("exclusion_reason", sa.String(255), nullable=True),
        sa.Column("source_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "distance_meters > 0", name=op.f("ck_activities_positive_distance")
        ),
        sa.CheckConstraint(
            "moving_time_seconds >= 0",
            name=op.f("ck_activities_nonnegative_moving_time"),
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_activities_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_activities"),
        sa.UniqueConstraint(
            "source", "external_activity_id", name="uq_activity_source_external_id"
        ),
    )
    op.create_index("ix_activities_user_id", "activities", ["user_id"])
    op.create_index("ix_activities_source", "activities", ["source"])
    op.create_index("ix_activities_started_at", "activities", ["started_at"])
    op.create_index("ix_activities_is_eligible", "activities", ["is_eligible"])


def downgrade() -> None:
    op.drop_table("activities")
    op.drop_table("strava_connections")
    op.drop_table("challenge_enrollments")
    op.drop_table("challenges")
    op.drop_table("users")

    bind = op.get_bind()
    activity_source.drop(bind, checkfirst=True)
    enrollment_status.drop(bind, checkfirst=True)
    challenge_status.drop(bind, checkfirst=True)
