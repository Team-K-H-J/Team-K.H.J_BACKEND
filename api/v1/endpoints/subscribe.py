from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.auth_session import get_current_user
from database.connection import Create_db
from models.devices import Devices
from models.operations import Cycle_User
from models.state import State
from models.subscribe import Subscribe
from models.subscribe_log import Subscribe_log
from models.users import Users
from Schemas.subscribe_schema import user_want_device
from services.common import utcnow
from services.devices import active_cycle, locked_device, runtime_for

router_subscribe = APIRouter()


def is_subscribed(user_id: bytes, user_device: str, db: Session):
    return db.scalar(select(Subscribe).where(Subscribe.user_id == user_id, Subscribe.device_id == user_device).with_for_update())


@router_subscribe.post("/api/v1/subscribe/add")
def subscribe_add(user_device: user_want_device, db: Session = Depends(Create_db), user_data: Users = Depends(get_current_user)):
    locked_device(db, user_device.device_id)
    runtime = runtime_for(db, user_device.device_id)
    state = db.scalar(select(State).where(State.device_id == user_device.device_id).with_for_update())
    if runtime.unavailable or state is None or state.state != "used":
        raise HTTPException(409, "사용 중인 건조기만 구독할 수 있습니다.")
    if is_subscribed(user_data.user_id, user_device.device_id, db):
        return {"success": False, "message": "잘못된 요청"}
    now = utcnow()
    db.add(Subscribe(user_id=user_data.user_id, device_id=user_device.device_id))
    db.add(Subscribe_log(user_id=user_data.user_id, device_id=user_device.device_id, state="subscribed", created_at=now))
    cycle = active_cycle(db, user_device.device_id)
    if cycle and db.get(Cycle_User, (cycle.id, user_data.user_id)) is None:
        db.add(Cycle_User(cycle_id=cycle.id, user_id=user_data.user_id, subscribed_at=now))
    db.commit()
    return {"success": True, "message": "알람 설정 완료"}


def remove_subscription(device_id: str, user: Users, db: Session):
    locked_device(db, device_id)
    subscription = is_subscribed(user.user_id, device_id, db)
    if subscription is None:
        return {"success": False, "message": "잘못된 요청"}
    db.delete(subscription)
    db.add(Subscribe_log(user_id=user.user_id, device_id=device_id, state="not_subscribed", created_at=utcnow()))
    db.commit()
    return {"success": True, "message": "알람 설정 삭제 완료"}


@router_subscribe.delete("/api/v1/subscribe/delete")
def subscribe_delete(user_device: user_want_device, db: Session = Depends(Create_db), user_data: Users = Depends(get_current_user)):
    return remove_subscription(user_device.device_id, user_data, db)


@router_subscribe.delete("/api/v1/subscribe/delete/{device_name}")
def subscribe_delete_by_name(device_name: str, user_device: user_want_device | None = None,
                             db: Session = Depends(Create_db), user_data: Users = Depends(get_current_user)):
    device = db.scalar(select(Devices).where(Devices.device_name == device_name))
    if device is None:
        device = db.get(Devices, device_name)
    if device is None:
        raise HTTPException(404, "장치가 존재하지 않습니다.")
    if user_device and user_device.device_id != device.device_id:
        raise HTTPException(422, "경로와 본문의 장치가 일치하지 않습니다.")
    return remove_subscription(device.device_id, user_data, db)
