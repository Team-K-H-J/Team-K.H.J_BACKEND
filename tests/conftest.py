import hashlib
import os
from pathlib import Path
import sys

import pytest
from dotenv import dotenv_values
from fastapi.testclient import TestClient
from pwdlib import PasswordHash
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["WORKER_ENABLED"] = "false"
os.environ["EMAIL_CODE_SECRET"] = "integration-test-secret-isolated-from-real-service"

import models  # noqa: F401 -- register models or load environment
from database.base import Base
from database.connection import Create_db
from main import app
from models.devices import Devices
from models.operations import Device_Credential, Device_Runtime
from models.state import State
from models.users import Users
from services.common import utcnow

PASSWORD = "TestPassword-123!"
PASSWORD_HASH = PasswordHash.recommended().hash(PASSWORD)


@pytest.fixture(scope="session")
def test_engine():
    url = os.getenv("TEST_DATABASE_URL")
    if os.getenv("TEST_USE_MYSQL") == "1" and not url:
        url = dotenv_values(ROOT / ".local" / "test-database.env").get("TEST_DATABASE_URL")
        if not url:
            pytest.fail("Workspace test database is not configured.")
    if url:
        engine = create_engine(url, hide_parameters=True)
        if engine.url.database != "jhy_test" or engine.url.host not in {"localhost", "127.0.0.1"}:
            raise RuntimeError("Tests require the dedicated local jhy_test database.")
        from alembic import command
        from alembic.config import Config
        with engine.begin() as connection:
            cfg = Config(str(ROOT / "alembic.ini"))
            cfg.attributes["connection"] = connection
            command.upgrade(cfg, "head")
    else:
        engine = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}, hide_parameters=True)
        @event.listens_for(engine, "connect")
        def sqlite_fk(connection, record):
            connection.isolation_level = None
            connection.execute("PRAGMA foreign_keys=ON")
        @event.listens_for(engine, "begin")
        def sqlite_begin(connection):
            connection.exec_driver_sql("BEGIN")
        Base.metadata.create_all(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db(test_engine):
    with test_engine.connect() as connection:
        transaction = connection.begin()
        session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
        yield session
        session.close()
        transaction.rollback()


@pytest.fixture(autouse=True)
def fake_smtp(monkeypatch):
    messages = []
    class SMTP:
        def __init__(self, *args, **kwargs):
            pass
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def login(self, *args):
            pass
        def send_message(self, message):
            messages.append(message)
    monkeypatch.setenv("GMAIL_ADDRESS", "sender@example.com")
    monkeypatch.setenv("GMAIL_APP_PASSWORD", "mock-smtp-password")
    monkeypatch.setenv("ADMIN_EMAILS", "admin@example.com")
    monkeypatch.delenv("FCM_PROJECT_ID", raising=False)
    monkeypatch.setattr("auth.auth_email.smtplib.SMTP_SSL", SMTP)
    return messages


@pytest.fixture
def client(db):
    def get_db():
        yield db
    app.dependency_overrides[Create_db] = get_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear()


@pytest.fixture
def users(db):
    result = []
    for index, email in enumerate(("user@example.com", "second@example.com", "admin@example.com")):
        row = Users(email=email, password_hash=PASSWORD_HASH + "" if index == 0 else PasswordHash.recommended().hash(PASSWORD),
                    name="사용자" + str(index), number="111" + str(index))
        db.add(row)
        db.flush()
        result.append(row)
    db.commit()
    return result


@pytest.fixture
def device(db):
    row = Devices(device_id="dryer-01", device_name="1번 건조기")
    db.add(row)
    db.flush()
    db.add_all([State(device_id=row.device_id, state="not_used", updated_at=utcnow()),
                Device_Runtime(device_id=row.device_id, unavailable=False, cycle_status="not_used", last_seen_at=utcnow()),
                Device_Credential(device_id=row.device_id, key_hash=hashlib.sha256(b"test-device-key").hexdigest())])
    db.commit()
    return row


def login(client, email="user@example.com"):
    result = client.post("/api/v1/users/login", json={"email": email, "password": PASSWORD})
    assert result.status_code == 200, result.text
    return result


def telemetry(state="used", **extra):
    return {"state": state, "Vibration": state == "used", "Current": state == "used",
            "V_Data_before": [0, 0, 1], "V_Data_After": [1, 0, 1], "C_Data": "16.6", **extra}


def report(client, body):
    return client.patch("/api/v1/state/dryer-01", json=body, headers={"X-Device-Key": "test-device-key"})
