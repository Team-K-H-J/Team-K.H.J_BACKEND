"""Environment settings; never replace an existing process environment value."""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(Path(os.getenv("JHY_ENV_FILE", str(BASE_DIR / ".env"))))


def flag(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"true", "1", "yes"}


def admin_emails() -> set[str]:
    return {value.strip().lower() for value in os.getenv("ADMIN_EMAILS", "").split(",") if value.strip()}
