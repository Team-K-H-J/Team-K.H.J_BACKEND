from datetime import datetime

from sqlalchemy import BINARY, Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from database.base import Base
from database.types import UTCDateTime


class User_Profile(Base):
    __tablename__ = "user_profile"
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    image_url: Mapped[str | None] = mapped_column(String(2048))


class User_Settings(Base):
    __tablename__ = "user_settings"
    user_id: Mapped[bytes] = mapped_column(BINARY(16), ForeignKey("users.user_id", ondelete="CASCADE"), primary_key=True)
    notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    vibration_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    theme: Mapped[str] = mapped_column(String(8), default="system")
    completed: Mapped[bool] = mapped_column(Boolean, default=True)
    paused: Mapped[bool] = mapped_column(Boolean, default=True)
    stopped: Mapped[bool] = mapped_column(Boolean, default=True)
    _legacy_uncollected: Mapped[bool] = mapped_column("uncollected", Boolean, default=False, deferred=True)


class Email_Verification(Base):
    __tablename__ = "email_verification"
    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    purpose: Mapped[str] = mapped_column(String(16), primary_key=True)
    code_hash: Mapped[str] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime)
    sent_at: Mapped[datetime] = mapped_column(UTCDateTime)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    verified_at: Mapped[datetime | None] = mapped_column(UTCDateTime)


class Login_Attempt(Base):
    __tablename__ = "login_attempt"
    email: Mapped[str] = mapped_column(String(255), primary_key=True)
    failures: Mapped[int] = mapped_column(Integer, default=0)
    locked_until: Mapped[datetime | None] = mapped_column(UTCDateTime)
