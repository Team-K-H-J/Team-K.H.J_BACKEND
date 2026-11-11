from datetime import datetime
from uuid import uuid4

from sqlalchemy import BINARY, JSON, Boolean, ForeignKey, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.types import UTCDateTime


class Device_Runtime(Base):
    __tablename__ = "device_runtime"
    device_id: Mapped[str] = mapped_column(String(24), ForeignKey("devices.device_id"), primary_key=True)
    unavailable: Mapped[bool] = mapped_column(Boolean, default=False)
    unavailable_reason: Mapped[str | None] = mapped_column(String(255))
    sensor_error: Mapped[str | None] = mapped_column(String(255))
    _legacy_door_open: Mapped[bool | None] = mapped_column("door_open", Boolean, deferred=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    last_measured_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    _legacy_last_door_measured_at: Mapped[datetime | None] = mapped_column(
        "last_door_measured_at", UTCDateTime, deferred=True,
    )
    cycle_status: Mapped[str] = mapped_column(String(16), default="not_used")
    expected_seconds: Mapped[int] = mapped_column(Integer, default=2400)


class Device_Credential(Base):
    __tablename__ = "device_credential"
    device_id: Mapped[str] = mapped_column(String(24), ForeignKey("devices.device_id"), primary_key=True)
    key_hash: Mapped[str] = mapped_column(String(64))


class Drying_Cycle(Base):
    __tablename__ = "drying_cycle"
    __table_args__ = (Index("ix_cycle_device_started", "device_id", "started_at"),)
    id: Mapped[bytes] = mapped_column(BINARY(16), primary_key=True, default=lambda: uuid4().bytes)
    device_id: Mapped[str] = mapped_column(String(24), ForeignKey("devices.device_id"))
    started_at: Mapped[datetime] = mapped_column(UTCDateTime)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    _legacy_collected_at: Mapped[datetime | None] = mapped_column("collected_at", UTCDateTime, deferred=True)
    outcome: Mapped[str | None] = mapped_column(String(16))


class Cycle_User(Base):
    __tablename__ = "cycle_user"
    cycle_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("drying_cycle.id"), primary_key=True)
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    subscribed_at: Mapped[datetime] = mapped_column(UTCDateTime)


class Telemetry_Event(Base):
    __tablename__ = "telemetry_event"
    __table_args__ = (Index("ix_telemetry_device_measured", "device_id", "measured_at"),)
    device_id: Mapped[str] = mapped_column(String(24), ForeignKey("devices.device_id"), primary_key=True)
    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    measured_at: Mapped[datetime] = mapped_column(UTCDateTime)
    received_at: Mapped[datetime] = mapped_column(UTCDateTime)
    payload_hash: Mapped[str] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON)
