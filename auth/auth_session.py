import secrets
from datetime import timedelta

from fastapi import Depends, HTTPException, Request, Response, Security
from fastapi.security import APIKeyCookie
from sqlalchemy.orm import Session

from config import flag
from database.connection import Create_db
from models.session_model import Session_Model
from models.users import Users
from services.common import utc, utcnow

session_cookie = APIKeyCookie(name="session_id", scheme_name="SessionCookie", auto_error=False)


def check_session(session_id: str, db: Session, allow_reset: bool = False) -> Users | None:
    user_session = db.get(Session_Model, session_id)
    if user_session is None:
        return None
    if utc(user_session.expired_at) <= utcnow():
        db.delete(user_session)
        db.commit()
        return None
    if user_session.purpose != "login" and not allow_reset:
        return None
    return db.get(Users, user_session.user_id)


def request_session_id(request: Request) -> str | None:
    return request.cookies.get("session_id") or request.cookies.get("Session_id")


def get_current_user(request: Request, db: Session = Depends(Create_db),
                     session_id: str | None = Security(session_cookie)) -> Users:
    session_id = request_session_id(request)
    user = check_session(session_id, db) if session_id else None
    if user is None:
        raise HTTPException(401, "유효하지 않거나 만료된 세션입니다.")
    return user


def delete_session(session_id: str, db: Session) -> None:
    user_session = db.get(Session_Model, session_id)
    if user_session is not None:
        db.delete(user_session)
        db.commit()


def create_session(user: Users, response: Response, db: Session, purpose: str = "login"):
    token = secrets.token_urlsafe(32)
    now = utcnow()
    lifetime = 600 if purpose == "reset" else 86400
    db.add(Session_Model(session_id=token, user_id=user.user_id, created_at=now,
                         expired_at=now + timedelta(seconds=lifetime), purpose=purpose))
    db.commit()
    response.set_cookie(key="session_id", value=token, max_age=lifetime,
                        httponly=True, secure=flag("COOKIE_SECURE"), samesite="lax", path="/")
    return token

