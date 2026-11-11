
from sqlalchemy import ForeignKey, String, BINARY, Index
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base


class Subscribe(Base):
    __tablename__ = "subscribe"
    __table_args__ = (Index("ix_subscribe_user_device", "user_id", "device_id"),)

    device_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("devices.device_id"),
        primary_key=True,
    )

    user_id: Mapped[bytes] = mapped_column(
        BINARY(16),
        ForeignKey("users.user_id"),
        primary_key=True,
        nullable=False,
    )
"""
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
    )

    subscribe_state: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        server_default="not_subscribed",
    ) 
    """
