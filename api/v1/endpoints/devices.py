from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.auth_admin import get_admin
from auth.auth_session import get_current_user
from database.connection import Create_db
from models.devices import Devices
from models.operations import Cycle_User, Drying_Cycle
from models.state_log import State_log
from models.users import Users
from Schemas.application import AvailabilityPatch
from services.common import iso
from services.devices import cycle_view, device_view, locked_device, runtime_for

router_devices = APIRouter()


@router_devices.get("/api/v1/devices")
def list_devices(q: str = Query("", max_length=100),
                 state: str | None = None, available: bool | None = None,
                 db: Session = Depends(Create_db)):
    devices = db.scalars(select(Devices).order_by(Devices.device_id)).all()
    items = [device_view(db, device) for device in devices
             if q.lower() in device.device_id.lower() or q.lower() in device.device_name.lower()]
    return [item for item in items if (state is None or item["state"] == state)
            and (available is None or item["available"] == available)]


@router_devices.get("/api/v1/devices/{device_id}")
def device_detail(device_id: str, db: Session = Depends(Create_db)):
    device = db.get(Devices, device_id)
    if device is None:
        raise HTTPException(404, "장치가 존재하지 않습니다.")
    return device_view(db, device)


@router_devices.get("/api/v1/users/me/history")
def user_history(device_id: str | None = None, limit: int = Query(50, ge=1, le=100),
                 offset: int = Query(0, ge=0), db: Session = Depends(Create_db),
                 user: Users = Depends(get_current_user)):
    query = select(Drying_Cycle).join(Cycle_User).where(Cycle_User.user_id == user.user_id)
    if device_id:
        query = query.where(Drying_Cycle.device_id == device_id)
    return [cycle_view(cycle) for cycle in db.scalars(query.order_by(Drying_Cycle.started_at.desc()).offset(offset).limit(limit))]


@router_devices.get("/api/v1/users/me/history/{cycle_id}")
def user_cycle(cycle_id: UUID, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    if db.get(Cycle_User, (cycle_id.bytes, user.user_id)) is None:
        raise HTTPException(404, "사용 기록이 존재하지 않습니다.")
    return cycle_view(db.get(Drying_Cycle, cycle_id.bytes))


@router_devices.get("/api/v1/admin/devices", dependencies=[Depends(get_admin)])
def admin_devices(db: Session = Depends(Create_db)):
    return [device_view(db, device) for device in db.scalars(select(Devices).order_by(Devices.device_id))]


@router_devices.get("/api/v1/admin/devices/{device_id}", dependencies=[Depends(get_admin)])
def admin_device(device_id: str, db: Session = Depends(Create_db)):
    return device_detail(device_id, db)


@router_devices.patch("/api/v1/admin/devices/{device_id}/availability", dependencies=[Depends(get_admin)])
def change_availability(device_id: str, data: AvailabilityPatch, db: Session = Depends(Create_db)):
    device = locked_device(db, device_id)
    runtime = runtime_for(db, device_id)
    if runtime.unavailable == data.unavailable:
        raise HTTPException(409, "이미 요청한 이용 가능 상태입니다.")
    runtime.unavailable = data.unavailable
    runtime.unavailable_reason = data.reason if data.unavailable else None
    db.commit()
    return device_view(db, device)


@router_devices.get("/api/v1/admin/devices/{device_id}/history", dependencies=[Depends(get_admin)])
def admin_history(device_id: str, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                  db: Session = Depends(Create_db)):
    if db.get(Devices, device_id) is None:
        raise HTTPException(404, "장치가 존재하지 않습니다.")
    cycles = db.scalars(select(Drying_Cycle).where(Drying_Cycle.device_id == device_id)
                        .order_by(Drying_Cycle.started_at.desc()).offset(offset).limit(limit))
    logs = db.scalars(select(State_log).where(State_log.device_id == device_id)
                      .order_by(State_log.created_at.desc(), State_log.state_log_id.desc()).offset(offset).limit(limit))
    return {"cycles": [cycle_view(cycle) for cycle in cycles],
            "state_changes": [{"id": log.state_log_id, "state": log.state, "created_at": iso(log.created_at)} for log in logs]}
