from datetime import datetime, timezone
from uuid import UUID


def utcnow() -> datetime:
    # MySQL DATETIME stores no timezone. Database timestamps are UTC.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def iso(value: datetime | None) -> str | None:
    return utc(value).isoformat() + "Z" if value else None


def uid(value: bytes) -> str:
    return str(UUID(bytes=value))
