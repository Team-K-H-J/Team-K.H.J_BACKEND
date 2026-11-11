import asyncio
from datetime import timedelta
import logging
import os
from functools import lru_cache

import google.auth
from google.auth.transport.requests import Request as GoogleRequest
import httpx
from sqlalchemy import and_, exists, or_, select
from sqlalchemy.orm import Session

from database.connection import SessionLocal
from models.account import User_Settings
from models.notification import NOTIFICATION_KINDS, Notification, Push_Token, Push_Delivery
from models.session_model import Session_Model
from services.common import iso, uid, utcnow

logger = logging.getLogger(__name__)


def notification_view(row):
    return {"id": uid(row.id), "device_id": row.device_id, "cycle_id": uid(row.cycle_id) if row.cycle_id else None,
            "kind": row.kind, "message": row.message, "created_at": iso(row.created_at),
            "read_at": iso(row.read_at), "read": row.read_at is not None}


@lru_cache(maxsize=1)
def push_credentials():
    credentials, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/firebase.messaging"])
    return credentials


def send_push(token: str, row):
    project = os.getenv("FCM_PROJECT_ID")
    if not project:
        raise RuntimeError("FCM is not configured")
    credentials = push_credentials()
    if not credentials.valid:
        transport = GoogleRequest()
        def bounded_request(*args, **kwargs):
            kwargs["timeout"] = 10
            return transport(*args, **kwargs)
        credentials.refresh(bounded_request)
    notification_id = uid(row.id)
    response = httpx.post(
        f"https://fcm.googleapis.com/v1/projects/{project}/messages:send",
        headers={"Authorization": f"Bearer {credentials.token}"},
        json={"message": {"token": token,
              "notification": {"title": "J.H.Y", "body": row.message},
              "data": {"notification_id": notification_id, "device_id": row.device_id, "kind": row.kind},
              "android": {"collapse_key": notification_id},
              "apns": {"headers": {"apns-collapse-id": notification_id}}}},
        timeout=10,
    )
    if response.status_code == 404:
        try:
            if any(item.get("errorCode") == "UNREGISTERED" for item in response.json().get("error", {}).get("details", [])):
                return "unregistered"
        except (ValueError, TypeError):
            pass
    response.raise_for_status()
    return "sent"


def deliver_pending(db: Session):
    if not os.getenv("FCM_PROJECT_ID"):
        return
    now = utcnow()
    eligible_token = exists(select(Push_Token.token).outerjoin(Session_Model, Push_Token.session_id == Session_Model.session_id).where(
        Push_Token.user_id == Notification.user_id,
        or_(Push_Token.session_id.is_(None), Session_Model.expired_at > now)))
    enabled_kind = or_(*[and_(Notification.kind == kind, getattr(User_Settings, kind).is_(True))
                         for kind in NOTIFICATION_KINDS])
    pending = list(db.scalars(select(Notification).outerjoin(User_Settings, User_Settings.user_id == Notification.user_id).where(
        Notification.kind.in_(NOTIFICATION_KINDS),
        Notification.delivered_at.is_(None), Notification.delivery_attempts < 5,
        eligible_token,
        or_(User_Settings.user_id.is_(None), and_(User_Settings.notifications_enabled.is_(True), enabled_kind)),
        or_(Notification.next_attempt_at.is_(None), Notification.next_attempt_at <= now))
        .order_by(Notification.created_at).limit(20).with_for_update(skip_locked=True)))
    for row in pending:
        settings = db.get(User_Settings, row.user_id)
        if settings and (not settings.notifications_enabled or not getattr(settings, row.kind)):
            continue
        tokens = list(db.scalars(select(Push_Token).outerjoin(Session_Model, Push_Token.session_id == Session_Model.session_id).where(
            Push_Token.user_id == row.user_id, or_(Push_Token.session_id.is_(None), Session_Model.expired_at > now))))
        if not tokens:
            continue
        row.delivery_attempts += 1
        all_delivered = True
        for token in tokens:
            if db.get(Push_Delivery, (row.id, token.token)) is not None:
                continue
            try:
                result = send_push(token.token, row)
                if result == "unregistered":
                    db.delete(token)
                else:
                    db.add(Push_Delivery(notification_id=row.id, token=token.token, delivered_at=now))
            except Exception:
                # Provider errors can contain tokens. Never log their content.
                logger.warning("Push delivery failed; retry scheduled.")
                all_delivered = False
        if all_delivered:
            row.delivered_at = now
        else:
            row.next_attempt_at = now + timedelta(seconds=min(3600, 30 * 2 ** row.delivery_attempts))
    db.commit()


def tick():
    with SessionLocal() as db:
        deliver_pending(db)


async def worker(stop: asyncio.Event):
    while not stop.is_set():
        try:
            await asyncio.to_thread(tick)
        except Exception:
            logger.warning("Notification worker could not complete this iteration.")
        try:
            await asyncio.wait_for(stop.wait(), timeout=5)
        except TimeoutError:
            pass

