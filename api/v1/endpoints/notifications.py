import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.auth_session import check_session, get_current_user, request_session_id
from database.connection import Create_db, SessionLocal
from models.notification import NOTIFICATION_KINDS, Notification, Push_Token
from models.users import Users
from Schemas.application import PushTokenData
from services.common import utcnow
from services.notifications import notification_view

router_notifications = APIRouter()


@router_notifications.get("/api/v1/notifications")
def notifications(unread: bool = False, limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                  db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    query = select(Notification).where(Notification.user_id == user.user_id, Notification.kind.in_(NOTIFICATION_KINDS))
    if unread:
        query = query.where(Notification.read_at.is_(None))
    return [notification_view(row) for row in db.scalars(query.order_by(Notification.created_at.desc(), Notification.id.desc())
                                                        .offset(offset).limit(limit))]


@router_notifications.get("/api/v1/notifications/stream")
def notification_stream(request: Request, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    token, user_id = request_session_id(request), user.user_id
    db.rollback()

    async def events():
        seen = set()
        while not await request.is_disconnected():
            with SessionLocal() as session:
                if check_session(token, session) is None:
                    return
                rows = list(session.scalars(select(Notification).where(
                    Notification.user_id == user_id, Notification.kind.in_(NOTIFICATION_KINDS))
                                            .order_by(Notification.created_at.desc()).limit(100)))
                values = [notification_view(row) for row in reversed(rows) if row.id not in seen]
                seen.update(row.id for row in rows)
            for value in values:
                yield "id: " + value["id"] + "\nevent: notification\ndata: " + json.dumps(value, ensure_ascii=False) + "\n\n"
            yield ": keepalive\n\n"
            await asyncio.sleep(2)

    return StreamingResponse(events(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router_notifications.patch("/api/v1/notifications/{notification_id}/read")
def read_notification(notification_id: UUID, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    row = db.get(Notification, notification_id.bytes)
    if row is None or row.user_id != user.user_id or row.kind not in NOTIFICATION_KINDS:
        raise HTTPException(404, "알림이 존재하지 않습니다.")
    if row.read_at is None:
        row.read_at = utcnow()
        db.commit()
    return notification_view(row)


@router_notifications.post("/api/v1/users/me/push-tokens")
def register_token(request: Request, data: PushTokenData, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    token = db.get(Push_Token, data.token)
    if token is not None and token.user_id != user.user_id:
        raise HTTPException(409, "다른 계정에 등록된 토큰입니다. 해당 계정에서 먼저 해제해 주세요.")
    if token is None:
        db.add(Push_Token(token=data.token, user_id=user.user_id, session_id=request_session_id(request)))
    else:
        token.session_id = request_session_id(request)
    db.commit()
    return {"success": True}


@router_notifications.delete("/api/v1/users/me/push-tokens")
def remove_token(data: PushTokenData, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    token = db.get(Push_Token, data.token)
    if token is not None and token.user_id == user.user_id:
        db.delete(token)
        db.commit()
    return {"success": True}

