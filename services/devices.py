import hashlib
import hmac
import json
import os
from datetime import timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.account import User_Settings
from models.devices import Devices
from models.notification import Notification
from models.operations import (
    Device_Credential,
    Device_Runtime,
    Drying_Cycle,
    Telemetry_Event,
)
from models.state import State
from models.state_log import State_log
from models.subscribe import Subscribe
from models.subscribe_log import Subscribe_log
from services.common import iso, uid, utc, utcnow


def locked_device(db: Session, device_id: str):
    device = db.scalar(select(Devices).where(Devices.device_id == device_id).with_for_update())
    if device is None:
        raise HTTPException(404, "장치가 존재하지 않습니다.")
    return device


def require_device_key(db: Session, device_id: str, key: str | None):
    credential = db.get(Device_Credential, device_id)
    digest = hashlib.sha256((key or "").encode()).hexdigest()
    if credential is None or not key or not hmac.compare_digest(credential.key_hash, digest):
        raise HTTPException(401, "유효한 장치 인증키가 필요합니다.")


def runtime_for(db: Session, device_id: str):
    runtime = db.scalar(select(Device_Runtime).where(Device_Runtime.device_id == device_id)
                        .with_for_update().execution_options(populate_existing=True))
    if runtime is None:
        runtime = Device_Runtime(device_id=device_id, unavailable=False, cycle_status="not_used",
                                 expected_seconds=int(os.getenv("ESTIMATED_CYCLE_SECONDS", "2400")))
        db.add(runtime)
        db.flush()
    return runtime


def active_cycle(db: Session, device_id: str):
    return db.scalar(select(Drying_Cycle).where(Drying_Cycle.device_id == device_id,
                     Drying_Cycle.ended_at.is_(None)).order_by(Drying_Cycle.started_at.desc())
                     .with_for_update().execution_options(populate_existing=True))


def latest_cycle(db: Session, device_id: str):
    return db.scalar(select(Drying_Cycle).where(Drying_Cycle.device_id == device_id)
                     .order_by(Drying_Cycle.started_at.desc()).limit(1))


def notify(db: Session, user_id: bytes, device_id: str, cycle_id: bytes, kind: str, event_key: str, when):
    settings = db.get(User_Settings, user_id)
    if settings and (not settings.notifications_enabled or not getattr(settings, kind)):
        return
    if db.scalar(select(Notification.id).where(Notification.user_id == user_id, Notification.event_key == event_key)):
        return
    labels = {"completed": "건조가 완료되었습니다.", "paused": "건조기가 일시정지되었습니다.",
              "stopped": "건조기가 중단되었습니다."}
    db.add(Notification(user_id=user_id, device_id=device_id, cycle_id=cycle_id, kind=kind,
                        event_key=event_key, message=f"{device_id}: {labels[kind]}", created_at=when))


def payload_digest(payload: dict) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def record_event(db: Session, device_id: str, event_id: str, measured_at, payload: dict):
    digest = payload_digest(payload)
    previous = db.scalar(select(Telemetry_Event).where(Telemetry_Event.device_id == device_id,
                         Telemetry_Event.event_id == event_id).with_for_update())
    if previous:
        stored_digest = previous.payload_hash
        if "door_open" in previous.payload:
            # Replays of old telemetry should match even though this field is retired.
            stored_payload = previous.payload.copy()
            stored_payload.pop("door_open")
            stored_digest = payload_digest(stored_payload)
        if not hmac.compare_digest(stored_digest, digest):
            raise HTTPException(409, "같은 이벤트 ID에 다른 데이터가 전송되었습니다.")
        return False
    if measured_at > utcnow() + timedelta(minutes=5):
        raise HTTPException(422, "미래의 측정 시각은 허용되지 않습니다.")
    db.add(Telemetry_Event(device_id=device_id, event_id=event_id, measured_at=measured_at,
                           received_at=utcnow(), payload_hash=digest, payload=payload))
    return True


def apply_telemetry(db: Session, device_id: str, data):
    locked_device(db, device_id)
    if data.device_id and data.device_id != device_id:
        raise HTTPException(422, "경로와 본문의 장치 ID가 일치하지 않습니다.")
    when = utc(data.measured_at) if data.measured_at else utcnow()
    event_id = data.event_id or str(uuid4())
    payload = data.model_dump(mode="json")
    if payload.get("vibration_hz") is None:
        # Keep hashes from existing clients valid when they resend a stored event.
        payload.pop("vibration_hz", None)
    if not record_event(db, device_id, event_id, when, payload):
        db.commit()
        return False
    runtime = runtime_for(db, device_id)
    runtime.last_seen_at = utcnow()
    if runtime.last_measured_at and when < runtime.last_measured_at:
        db.commit()
        return False
    state = db.scalar(select(State).where(State.device_id == device_id).with_for_update()
                      .execution_options(populate_existing=True))
    old_state = state.state if state else "not_used"
    runtime.last_measured_at = when
    runtime.sensor_error = data.sensor_error
    if data.state == "error" and not runtime.sensor_error:
        runtime.sensor_error = "센서 오류"
    cycle = active_cycle(db, device_id)
    if data.state == "used":
        if cycle is None:
            cycle = Drying_Cycle(device_id=device_id, started_at=when)
            db.add(cycle)
            db.flush()
        runtime.cycle_status = "used"
    elif data.state == "paused":
        runtime.cycle_status = "paused"
        if cycle and old_state != "paused":
            for subscription in db.scalars(select(Subscribe).where(Subscribe.device_id == device_id).with_for_update()):
                notify(db, subscription.user_id, device_id, cycle.id, "paused", uid(cycle.id) + ":" + event_id + ":paused", when)
    elif data.state == "error":
        runtime.cycle_status = "error"
    elif cycle:
        seconds = max(0, (when - cycle.started_at).total_seconds())
        cycle.ended_at = when
        cycle.outcome = "completed" if seconds >= 2400 else "stopped"
        runtime.cycle_status = cycle.outcome
        for subscription in list(db.scalars(select(Subscribe).where(Subscribe.device_id == device_id).with_for_update())):
            notify(db, subscription.user_id, device_id, cycle.id, cycle.outcome, uid(cycle.id) + ":" + cycle.outcome, when)
            db.add(Subscribe_log(user_id=subscription.user_id, device_id=device_id,
                                 state="not_subscribed", created_at=when))
            db.delete(subscription)
    if state is None:
        state = State(device_id=device_id, state=data.state, updated_at=when)
        db.add(state)
    else:
        state.state, state.updated_at = data.state, when
    if old_state != data.state:
        db.add(State_log(device_id=device_id, state=data.state, created_at=when))
    db.commit()
    return True


def device_view(db: Session, device: Devices, now=None):
    now = now or utcnow()
    runtime, state = db.get(Device_Runtime, device.device_id), db.get(State, device.device_id)
    cycle = latest_cycle(db, device.device_id)
    stale_seconds = int(os.getenv("DEVICE_STALE_SECONDS", "120"))
    online = bool(runtime and runtime.last_seen_at and (now - runtime.last_seen_at).total_seconds() <= stale_seconds)
    status = runtime.cycle_status if runtime else (state.state if state else "unknown")
    unavailable = bool(runtime and runtime.unavailable)
    sensor_error = runtime.sensor_error if runtime else None
    display_state = "unavailable" if unavailable else ("error" if sensor_error else status)
    duration = runtime.expected_seconds if runtime else int(os.getenv("ESTIMATED_CYCLE_SECONDS", "2400"))
    elapsed = max(0, int(((cycle.ended_at or now) - cycle.started_at).total_seconds())) if cycle else None
    running = cycle is not None and cycle.ended_at is None
    remaining = max(0, duration - elapsed) if running else None
    return {
        "device_id": device.device_id, "device_name": device.device_name, "state": display_state,
        "available": online and not unavailable and not sensor_error and status in {"not_used", "completed", "stopped"},
        "unavailable": unavailable, "unavailable_reason": runtime.unavailable_reason if runtime else None,
        "sensor_error": sensor_error, "online": online, "communication_error": not online,
        "last_updated_at": iso(state.updated_at) if state else None,
        "last_seen_at": iso(runtime.last_seen_at) if runtime else None,
        "started_at": iso(cycle.started_at) if cycle else None,
        "expected_completed_at": iso(cycle.started_at + timedelta(seconds=duration)) if running else None,
        "remaining_seconds": remaining, "progress": min(1.0, elapsed / duration) if running else (1.0 if cycle and cycle.outcome == "completed" else 0.0),
        "time_is_estimated": True, "cycle_id": uid(cycle.id) if cycle else None,
        "subscriber_count": db.scalar(select(func.count()).select_from(Subscribe).where(Subscribe.device_id == device.device_id)),
    }


def cycle_view(cycle):
    return {"id": uid(cycle.id), "device_id": cycle.device_id, "started_at": iso(cycle.started_at),
            "ended_at": iso(cycle.ended_at), "outcome": cycle.outcome,
            "duration_seconds": int((cycle.ended_at - cycle.started_at).total_seconds()) if cycle.ended_at else None}

