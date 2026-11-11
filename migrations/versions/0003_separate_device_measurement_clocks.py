"""Separate the door and sensor measurement clocks.

Revision ID: 0003
Revises: 0002
"""

import sqlalchemy as sa
from alembic import op

from database.types import UTCDateTime

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("device_runtime", sa.Column("last_door_measured_at", UTCDateTime, nullable=True))
    op.create_index("ix_telemetry_device_measured", "telemetry_event", ["device_id", "measured_at"])

    runtime = sa.table("device_runtime", sa.column("device_id"), sa.column("door_open", sa.Boolean),
                       sa.column("last_measured_at"), sa.column("last_door_measured_at"))
    events = sa.table("telemetry_event", sa.column("device_id"), sa.column("measured_at"),
                      sa.column("payload", sa.JSON))
    state = sa.table("state", sa.column("device_id"), sa.column("updated_at"))

    # Preserve the door value currently visible and recover its measurement time from the archive.
    last_door = sa.select(sa.func.max(events.c.measured_at)).where(
        events.c.device_id == runtime.c.device_id,
        events.c.measured_at <= runtime.c.last_measured_at,
        events.c.payload["door_open"].as_string().is_not(None),
        events.c.payload["door_open"].as_boolean() == runtime.c.door_open,
    ).scalar_subquery()
    op.execute(runtime.update().where(runtime.c.door_open.is_not(None)).values(
        last_door_measured_at=sa.func.coalesce(last_door, runtime.c.last_measured_at),
    ))

    # A registered device's initial state can exist before its first sensor measurement.
    has_sensor_event = sa.select(1).where(
        events.c.device_id == state.c.device_id,
        events.c.measured_at == state.c.updated_at,
        events.c.payload["state"].as_string().is_not(None),
    ).exists()
    last_sensor = sa.select(state.c.updated_at).where(
        state.c.device_id == runtime.c.device_id, has_sensor_event,
    ).scalar_subquery()
    op.execute(runtime.update().where(runtime.c.last_measured_at.is_not(None)).values(
        last_measured_at=last_sensor,
    ))


def downgrade() -> None:
    raise RuntimeError("Destructive downgrade is intentionally disabled. Restore an approved backup instead.")
