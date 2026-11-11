from datetime import datetime
from uuid import uuid4

from sqlalchemy import BINARY, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.types import UTCDateTime


NOTIFICATION_KINDS = ("completed", "paused", "stopped")


class Notification(Base):
    __tablename__ = "notification"
    __table_args__ = (UniqueConstraint("user_id", "event_key", name="uq_notification_user_event"),)
    id: Mapped[bytes] = mapped_column(BINARY(16), primary_key=True, default=lambda: uuid4().bytes)
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    device_id: Mapped[str] = mapped_column(String(24), ForeignKey("devices.device_id"))
    cycle_id: Mapped[bytes | None] = mapped_column(BINARY(16), ForeignKey("drying_cycle.id"))
    event_key: Mapped[str] = mapped_column(String(128))
    kind: Mapped[str] = mapped_column(String(16))
    message: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    delivered_at: Mapped[datetime | None] = mapped_column(UTCDateTime)
    delivery_attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class Push_Token(Base):
    __tablename__ = "push_token"
    token: Mapped[str] = mapped_column(String(512), primary_key=True)
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.user_id", ondelete="CASCADE"), index=True)
    session_id: Mapped[str | None] = mapped_column(String(255), ForeignKey("session.session_id", ondelete="CASCADE"))


class Push_Delivery(Base):
    __tablename__ = "push_delivery"
    notification_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("notification.id", ondelete="CASCADE"), primary_key=True)
    token: Mapped[str] = mapped_column(String(512), ForeignKey("push_token.token", ondelete="CASCADE"), primary_key=True)
    delivered_at: Mapped[datetime] = mapped_column(UTCDateTime)
