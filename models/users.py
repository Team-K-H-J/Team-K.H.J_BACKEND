from sqlalchemy import String, BINARY
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4


from database.base import Base

class Users(Base):
    __tablename__ = "users"

    user_id: Mapped[bytes] = mapped_column(
        BINARY(16),
        primary_key=True,
        default=lambda: uuid4().bytes,
    )

    email: Mapped[str] = mapped_column(
            String(255),
            nullable=False,
            unique=True
    )

    password_hash: Mapped[str] = mapped_column(
            String(255),
            nullable=False,
            unique=True
    )

    name: Mapped[str] = mapped_column(
        String(24),
        nullable=False
    )


    number: Mapped[str] = mapped_column(
        String(4),
        nullable=False
    )
