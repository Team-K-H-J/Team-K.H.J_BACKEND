from fastapi import APIRouter, Depends
from Schemas.subscribe_schema import user_want_device
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.connection import Create_db
from models.users import Users
from auth.auth_session import get_current_user
from models.subscribe import Subscribe
from models.subscribe_log import Subscribe_log
from datetime import datetime
#------------------------------

#라우터 선언
router_subscribe = APIRouter()

#알람 설정이 되어있는지 확인하는 함수
def is_subscribed(user_id:str, user_device:str, db:Session):

    #구독 상태 조회
    user = db.scalar(
            select(Subscribe).where(Subscribe.user_id == user_id & Subscribe.device_id == user_device)
        )
    
    return user
    

#알림설정시 함수
@router_subscribe.post("/api/v1/subscribe/add")
def subscribe_add(user_device : user_want_device,db: Session = Depends(Create_db),user_data: Users = Depends(get_current_user)):

    now = datetime.now()

    #기존 알람 설정이 켜져있는지 확인
    result = is_subscribed(user_data.user_id,user_device.device_id,db)

    if result is not None:
        return {
            "success": False,
            "message": "잘못된 요청"
        }

    #db에 추가할 정보 객체 생성
    new_data = Subscribe(
        user_id = user_data.user_id,
        device_id = user_device.device_id
    )

    new_log = Subscribe_log(
        user_id = user_data.user_id,
        device_id = user_device.device_id,
        state = "subscribed",
        created_at = now
    )

    #db에 정보 추가
    db.add(new_data)
    db.add(new_log)
    db.commit()

    return {
        "success":True,
        "message":"알림 저장 성공"
    }

#알림설정 취소시 함수
@router_subscribe.delete("/api/v1/subscribe/delete")
def subscribe_add(user_device : user_want_device,db: Session = Depends(Create_db),user_data: Users = Depends(get_current_user)):

    now = datetime.now()

    #기존 알람 설정이 켜져있는지 확인
    result = is_subscribed(user_data.user_id,user_device.device_id,db)

    if result is not None:
        return {
            "success": False,
            "message": "잘못된 요청"
        }

    #데이터 삭제및 로그 저장
    db.delete(result)

    new_log = Subscribe_log(
        user_id = user_data.user_id,
        device_id = user_device.device_id,
        state = "not_subscribed",
        created_at = now
    )

    db.add(new_log)
    db.commit()

    return {
        "success": True,
        "message":"알림 삭제됨"
    }