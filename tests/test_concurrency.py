from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from uuid import uuid4

from fastapi.testclient import TestClient
from pwdlib import PasswordHash
import pytest
from sqlalchemy import delete, func, or_, select
from sqlalchemy.orm import Session

from conftest import PASSWORD, telemetry
from database.base import Base
from database.connection import Create_db
from main import app
from models.devices import Devices
from models.operations import Device_Credential, Device_Runtime, Drying_Cycle, Telemetry_Event
from models.state import State
from models.subscribe import Subscribe
from models.users import Users
from services.common import iso, utcnow
import hashlib


def test_mysql_simultaneous_subscribers_and_idempotent_events(test_engine):
    if test_engine.dialect.name != "mysql":
        pytest.skip("MySQL row locking is verified with TEST_USE_MYSQL=1.")
    suffix = uuid4().hex[:12]
    device_id = "race-" + suffix
    emails = ["race-" + suffix + f"-{index}@example.com" for index in range(2)]
    user_ids = []
    with Session(test_engine) as db:
        for index, email in enumerate(emails):
            user = Users(email=email, password_hash=PasswordHash.recommended().hash(PASSWORD), name="동시성테스트", number="1111")
            db.add(user)
            db.flush()
            user_ids.append(user.user_id)
        db.add(Devices(device_id=device_id, device_name=device_id))
        db.flush()
        db.add_all([State(device_id=device_id, state="used", updated_at=utcnow()),
                    Device_Runtime(device_id=device_id, cycle_status="used", last_seen_at=utcnow()),
                    Device_Credential(device_id=device_id, key_hash=hashlib.sha256(b"race-key").hexdigest()),
                    Drying_Cycle(device_id=device_id, started_at=utcnow())])
        db.commit()

    def get_db():
        with Session(test_engine) as session:
            try:
                yield session
            except Exception:
                session.rollback()
                raise

    app.dependency_overrides[Create_db] = get_db
    try:
        with TestClient(app) as first, TestClient(app) as second:
            for client, email in zip((first, second), emails):
                assert client.post("/api/v1/users/login", json={"email": email, "password": PASSWORD}).status_code == 200
            barrier = Barrier(2)
            def subscribe(client):
                barrier.wait()
                return client.post("/api/v1/subscribe/add", json={"device_id": device_id})
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(subscribe, client) for client in (first, second)]
                results = [future.result() for future in futures]
            assert all(result.status_code == 200 and result.json()["success"] for result in results)
            with Session(test_engine) as db:
                assert db.scalar(select(func.count()).select_from(Subscribe).where(Subscribe.device_id == device_id)) == 2

            body = telemetry(event_id="same-event", measured_at=iso(utcnow()))
            barrier = Barrier(2)
            def send_event(client):
                barrier.wait()
                return client.post(f"/api/v1/devices/{device_id}/events", json=body, headers={"X-Device-Key": "race-key"})
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(send_event, client) for client in (first, second)]
                results = [future.result() for future in futures]
            assert sorted(result.json()["applied"] for result in results) == [False, True]
            with Session(test_engine) as db:
                assert db.scalar(select(func.count()).select_from(Telemetry_Event).where(Telemetry_Event.device_id == device_id)) == 1

            barrier = Barrier(2)
            email = "signup-" + suffix + "@example.com"
            def request_email(client):
                barrier.wait()
                return client.post("/api/v1/signup/email", json={"email": email})
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(request_email, client) for client in (first, second)]
                results = [future.result() for future in futures]
            assert sorted(result.status_code for result in results) == [200, 429]
    finally:
        app.dependency_overrides.clear()
        # Only rows created above, in the dedicated local test database, are removed.
        with test_engine.begin() as connection:
            for table in reversed(Base.metadata.sorted_tables):
                conditions = []
                if "user_id" in table.c:
                    conditions.append(table.c.user_id.in_(user_ids))
                if "device_id" in table.c:
                    conditions.append(table.c.device_id == device_id)
                if "email" in table.c:
                    conditions.append(table.c.email.in_(emails + ["signup-" + suffix + "@example.com"]))
                if conditions:
                    connection.execute(delete(table).where(or_(*conditions)))
