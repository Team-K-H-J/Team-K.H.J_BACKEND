from datetime import datetime
from uuid import uuid4

from sqlalchemy import BINARY, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.types import UTCDateTime


class Inquiry(Base):
    __tablename__ = "inquiry"
    __table_args__ = (Index("ix_inquiry_status_created", "status", "created_at"),)
    id: Mapped[bytes] = mapped_column(BINARY(16), primary_key=True, default=lambda: uuid4().bytes)
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.user_id", ondelete="CASCADE"))
    device_id: Mapped[str | None] = mapped_column(String(24), ForeignKey("devices.device_id"))
    error_type: Mapped[str] = mapped_column(String(64))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="unread")
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)
