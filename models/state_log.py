from datetime import datetime

from sqlalchemy import ForeignKey, String, BigInteger, Integer, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.types import UTCDateTime


class State_log(Base):
    __tablename__ = "state_log"
    __table_args__ = (Index("ix_state_log_device_time_state", "device_id", "created_at", "state"),)

    state_log_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True
    )

    device_id: Mapped[str] = mapped_column(
        String(24),
        ForeignKey("devices.device_id"),
    )

    state: Mapped[str] = mapped_column(
        String(15),
        nullable=False,
        server_default="not_used",
    )

    created_at: Mapped[datetime] = mapped_column(
        UTCDateTime,
        nullable=False,
        server_default=func.now(),
    )
