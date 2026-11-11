from datetime import datetime
from uuid import uuid4

from sqlalchemy import BINARY, Boolean, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.types import UTCDateTime


class Notice(Base):
    __tablename__ = "notice"
    id: Mapped[bytes] = mapped_column(BINARY(16), primary_key=True, default=lambda: uuid4().bytes)
    author_id: Mapped[bytes | None] = mapped_column(BINARY(16), ForeignKey("users.user_id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    pinned: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime)
