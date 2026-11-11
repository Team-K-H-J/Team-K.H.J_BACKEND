from datetime import timedelta

import pytest
from conftest import login, report, telemetry
from sqlalchemy import func, select

from models.devices import Devices
from models.notification import Notification
from models.operations import Drying_Cycle, Telemetry_Event
from models.state import State
from models.subscribe import Subscribe
from services.common import iso, utcnow
from services.devices import payload_digest


def test_original_state_api_accepts_both_field_spellings(client, device, db):
    response = report(client, telemetry())
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "used"
    assert response.json()["data"]["deviceID"] == device.device_id
    old = telemetry()
    old["V_data_before"] = old.pop("V_Data_before")
    old["V_data_after"] = old.pop("V_Data_After")
    old["C_data"] = old.pop("C_Data")
    assert report(client, old).status_code == 200
    assert len(client.get("/api/v1/state/all").json()) == 1
    assert client.get("/api/v1/state/dryer-01").json()["state"] == "used"
    assert client.get("/api/v1/state/missing").status_code == 404


@pytest.mark.parametrize("change", [{"state": "invalid"}, {"Current": False}, {"C_Data": "NaN"},
                                    {"C_Data": "-1"}, {"V_Data_before": [1, 2]}, {"device_id": "other"}])
def test_invalid_sensor_data(client, device, change):
    assert report(client, telemetry(**change)).status_code == 422


def test_device_key_is_required(client, device):
    assert client.patch("/api/v1/state/dryer-01", json=telemetry()).status_code == 401
    assert client.patch("/api/v1/state/dryer-01", json=telemetry(), headers={"X-Device-Key": "bad"}).status_code == 401


def test_event_replay_conflicts_and_old_measurements(client, device, db):
    now = utcnow()
    body = telemetry(event_id="event-1", measured_at=iso(now))
    url = "/api/v1/devices/dryer-01/events"
    headers = {"X-Device-Key": "test-device-key"}
    assert client.post(url, json=body, headers=headers).json()["applied"] is True
    assert client.post(url, json=body, headers=headers).json()["applied"] is False
    event = db.get(Telemetry_Event, (device.device_id, "event-1"))
    assert "door_open" not in event.payload
    event.payload = {**event.payload, "door_open": None}
    event.payload_hash = payload_digest(event.payload)
    db.commit()
    assert client.post(url, json=body, headers=headers).json()["applied"] is False
    assert db.scalar(select(func.count()).select_from(Telemetry_Event)) == 1
    assert client.post(url, json={**body, "C_Data": "17"}, headers=headers).status_code == 409
    stale = telemetry("not_used", event_id="old", measured_at=iso(now - timedelta(seconds=1)))
    assert client.post(url, json=stale, headers=headers).json()["applied"] is False
    assert db.get(State, "dryer-01").state == "used"
    future = telemetry(event_id="future", measured_at=iso(now + timedelta(minutes=10)))
    assert client.post(url, json=future, headers=headers).status_code == 422


def test_esp32_frequency_measurement_sensor_error_and_recovery(client, device, db):
    url = "/api/v1/devices/dryer-01/events"
    headers = {"X-Device-Key": "test-device-key"}
    now = utcnow()
    sample = {"event_id": "reading", "measured_at": iso(now), "C_Data": 1.625,
              "Current": True, "Vibration": True, "vibration_hz": 12.5}

    assert client.post(url, json=sample).status_code == 401
    assert client.post(url, json={**sample, "C_Data": True}, headers=headers).status_code == 422
    assert client.post(url, json={**sample, "vibration_hz": -1}, headers=headers).status_code == 422
    assert client.post(url, json={**sample, "measured_at": "0001-01-01T00:00:00+01:00"}, headers=headers).status_code == 422
    assert client.post(url, json={**sample, "vibration_hz": None}, headers=headers).status_code == 422
    assert client.post(url, json={**sample, "V_Data_before": [0, 0, 1]}, headers=headers).status_code == 422
    assert report(client, sample).status_code == 422
    response = client.post(url, json=sample, headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["state"] == "used"
    assert response.json()["data"]["C_Data"] == "1.625"
    assert response.json()["data"]["vibration_hz"] == 12.5
    assert db.get(Telemetry_Event, ("dryer-01", "reading")).payload["vibration_hz"] == 12.5
    assert client.post(url, json=sample, headers=headers).json()["applied"] is False

    error = {"event_id": "fault", "measured_at": iso(now + timedelta(seconds=1)), "sensor_error": "MPU6050 timeout"}
    assert client.post(url, json=error, headers=headers).json()["data"]["state"] == "error"
    status = client.get("/api/v1/devices/dryer-01").json()
    assert status["state"] == "error" and status["sensor_error"] == "MPU6050 timeout"
    assert db.scalar(select(Drying_Cycle)).ended_at is None

    idle = {**sample, "event_id": "idle", "measured_at": iso(now + timedelta(seconds=2)),
            "C_Data": 0, "Current": False, "Vibration": False, "vibration_hz": 0}
    assert client.post(url, json=idle, headers=headers).json()["data"]["state"] == "not_used"
    status = client.get("/api/v1/devices/dryer-01").json()
    assert status["state"] == "stopped" and status["sensor_error"] is None


@pytest.mark.parametrize("duration,outcome", [(2399, "stopped"), (2400, "completed"), (3000, "completed")])
def test_cycle_boundary_multi_subscription_and_notifications(client, device, users, db, duration, outcome):
    now = utcnow()
    assert report(client, telemetry(measured_at=iso(now - timedelta(seconds=duration)))).status_code == 200
    login(client)
    assert client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"}).json()["success"] is True
    client.cookies.clear()
    login(client, users[1].email)
    assert client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"}).json()["success"] is True
    assert db.scalar(select(func.count()).select_from(Subscribe)) == 2
    assert report(client, telemetry("not_used", measured_at=iso(now))).status_code == 200
    assert db.scalar(select(func.count()).select_from(Subscribe)) == 0
    cycle = db.scalar(select(Drying_Cycle))
    assert cycle.outcome == outcome
    assert db.scalar(select(func.count()).select_from(Notification)) == 2
    assert client.get("/api/v1/notifications").json()[0]["kind"] == outcome
    status = client.get("/api/v1/devices/dryer-01").json()
    assert status["state"] == outcome and status["available"] is True
    history = client.get("/api/v1/users/me/history").json()
    assert history[0]["duration_seconds"] == duration
    assert "collected_at" not in history[0]
    assert client.get("/api/v1/users/me/history/" + history[0]["id"]).status_code == 200


def test_heartbeats_and_pause_do_not_reset_cycle(client, device, users, db):
    now = utcnow()
    report(client, telemetry(measured_at=iso(now - timedelta(minutes=20))))
    cycle = db.scalar(select(Drying_Cycle))
    started = cycle.started_at
    login(client)
    client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"})
    report(client, telemetry(measured_at=iso(now - timedelta(minutes=10))))
    report(client, telemetry("paused", event_id="pause", measured_at=iso(now - timedelta(minutes=5))))
    assert client.get("/api/v1/notifications").json()[0]["kind"] == "paused"
    report(client, telemetry(measured_at=iso(now)))
    assert db.scalar(select(func.count()).select_from(Drying_Cycle)) == 1
    assert cycle.started_at == started
    assert client.get("/api/v1/devices/dryer-01").json()["remaining_seconds"] <= 1200


def test_subscribe_cancel_only_own_and_documented_path(client, device, users, db):
    login(client)
    assert client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"}).status_code == 409
    report(client, telemetry())
    assert client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"}).json()["success"] is True
    assert client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"}).json()["success"] is False
    client.cookies.clear()
    login(client, users[1].email)
    assert client.request("DELETE", "/api/v1/subscribe/delete", json={"device_id": "dryer-01"}).json()["success"] is False
    assert db.scalar(select(func.count()).select_from(Subscribe)) == 1
    client.cookies.clear()
    login(client)
    response = client.request("DELETE", "/api/v1/subscribe/delete/1번 건조기", json={"device_id": "dryer-01"})
    assert response.json()["success"] is True
    assert db.scalar(select(func.count()).select_from(Subscribe)) == 0


def test_device_list_order_and_filtering(client, device, db):
    db.add(Devices(device_id="dryer-00", device_name="0번 건조기"))
    db.commit()
    items = client.get("/api/v1/devices").json()
    assert [item["device_id"] for item in items] == ["dryer-00", "dryer-01"]
    assert all("door_open" not in item and "favorite" not in item for item in items)
    assert len(client.get("/api/v1/devices?q=1번").json()) == 1
    assert client.get("/api/v1/devices?q=missing").json() == []


def test_notification_settings_are_respected(client, device, users):
    now = utcnow()
    report(client, telemetry(measured_at=iso(now - timedelta(minutes=45))))
    login(client)
    client.patch("/api/v1/users/me/settings", json={"completed": False})
    client.post("/api/v1/subscribe/add", json={"device_id": "dryer-01"})
    report(client, telemetry("not_used", measured_at=iso(now)))
    assert client.get("/api/v1/notifications").json() == []


def test_availability_override_survives_sensor_updates(client, device, users):
    login(client, "admin@example.com")
    url = "/api/v1/admin/devices/dryer-01/availability"
    assert client.patch(url, json={"unavailable": True, "reason": "점검"}).json()["state"] == "unavailable"
    assert client.patch(url, json={"unavailable": True}).status_code == 409
    report(client, telemetry())
    assert client.get("/api/v1/devices/dryer-01").json()["unavailable_reason"] == "점검"
    assert client.get("/api/v1/admin/devices/dryer-01/history").status_code == 200
    assert client.patch(url, json={"unavailable": False}).json()["state"] == "used"
