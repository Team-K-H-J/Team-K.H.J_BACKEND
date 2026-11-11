from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Response
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from auth.auth_admin import is_admin
from auth.auth_session import create_session
from database.connection import Create_db
from models.account import Login_Attempt
from models.users import Users
from Schemas.login_schema import LoginResponse, loginData
from services.common import utcnow

router_login = APIRouter()
password_hashing = PasswordHash.recommended()
_dummy_hash = password_hashing.hash("timing-padding-password")


def authenticate(login_data: loginData, db: Session) -> Users:
    email = str(login_data.email).lower()
    if db.get(Login_Attempt, email) is None:
        try:
            with db.begin_nested():
                db.add(Login_Attempt(email=email, failures=0))
                db.flush()
        except IntegrityError:
            pass
    attempt = db.scalar(select(Login_Attempt).where(Login_Attempt.email == email).with_for_update())
    now = utcnow()
    if attempt.locked_until and attempt.locked_until > now:
        raise HTTPException(429, "로그인 시도가 잠겼습니다. 10분 후 다시 시도해 주세요.")
    if attempt.locked_until:
        attempt.failures = 0
        attempt.locked_until = None
    user = db.scalar(select(Users).where(Users.email == email))
    try:
        valid = password_hashing.verify(login_data.password, user.password_hash if user else _dummy_hash)
    except (ValueError, UnknownHashError):
        valid = False
    if user is None or not valid:
        attempt.failures += 1
        if attempt.failures >= 10:
            attempt.locked_until = now + timedelta(minutes=10)
        db.commit()
        raise HTTPException(401, "아이디 또는 비밀번호가 올바르지 않습니다. 입력한 정보를 다시 확인해 주세요.")
    attempt.failures = 0
    attempt.locked_until = None
    db.commit()
    return user


@router_login.post("/api/v1/users/login", summary="관리자·일반 사용자 공통 로그인")
def login(login_data: loginData, response: Response, db: Session = Depends(Create_db)) -> LoginResponse:
    user = authenticate(login_data, db)
    create_session(user, response, db)
    return LoginResponse(message="로그인 성공", is_admin=is_admin(user))
