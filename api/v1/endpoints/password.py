from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security
from pwdlib import PasswordHash
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from auth.auth_email import make_and_send_email_number, check_email_number
from auth.auth_session import create_session, get_current_user, request_session_id, check_session
from auth.auth_session import session_cookie
from database.connection import Create_db
from models.account import Email_Verification, Login_Attempt
from models.users import Users
from models.session_model import Session_Model
from models.notification import Push_Token
from Schemas.forget_password import password_forget
from Schemas.email_code_schema import email_code_schema
from Schemas.auth_password import password_schema, new_password_schema
from services.common import utcnow

router_password = APIRouter()
password_hashing = PasswordHash.recommended()


@router_password.post("/api/v1/forget/password")
def forget_password(user_data: password_forget, db: Session = Depends(Create_db)):
    user = db.scalar(select(Users).where(Users.email == str(user_data.email).lower()))
    if user is None or user.number != user_data.number or user.name != user_data.name:
        return {"success": False, "message": "입력한 사용자 정보가 일치하지 않습니다."}
    return make_and_send_email_number(user_data.email, db, purpose="reset")


@router_password.post("/api/v1/forget/check/email_code")
def forget_check_email_code(response: Response, user_code: email_code_schema, db: Session = Depends(Create_db)):
    result = check_email_number(user_code, db, purpose="reset")
    if not result["success"]:
        return result
    email = str(user_code.email).lower()
    user = db.scalar(select(Users).where(Users.email == email))
    if user is None:
        raise HTTPException(404, "사용자가 존재하지 않습니다.")
    record = db.get(Email_Verification, (email, "reset"))
    db.delete(record)
    db.commit()
    create_session(user, response, db, purpose="reset")
    return result


@router_password.post("/api/v1/change/password_auth")
def auth_password_change(request: Request, user_know: password_schema,
                         db: Session = Depends(Create_db), user_data: Users = Depends(get_current_user)):
    if not password_hashing.verify(user_know.password, user_data.password_hash):
        return {"success": False, "message": "비밀번호가 일치하지 않습니다."}
    session = db.get(Session_Model, request_session_id(request))
    session.password_verified_at = utcnow()
    db.commit()
    return {"success": True, "message": "비밀번호가 일치함"}


@router_password.post("/api/v1/change/password")
def change_password(request: Request, response: Response, user_want: new_password_schema,
                    db: Session = Depends(Create_db), session_id: str | None = Security(session_cookie)):
    token = request_session_id(request)
    user = check_session(token, db, allow_reset=True) if token else None
    if user is None:
        raise HTTPException(401, "본인 인증이 필요합니다.")
    session = db.get(Session_Model, token)
    if session.purpose != "reset" and (
        session.password_verified_at is None or session.password_verified_at < utcnow() - timedelta(minutes=5)
    ):
        raise HTTPException(403, "기존 비밀번호 인증이 필요합니다.")
    user.password_hash = password_hashing.hash(user_want.password)
    db.execute(delete(Push_Token).where(Push_Token.user_id == user.user_id))
    db.execute(delete(Session_Model).where(Session_Model.user_id == user.user_id))
    db.execute(delete(Login_Attempt).where(Login_Attempt.email == user.email))
    db.commit()
    response.delete_cookie("session_id", path="/")
    response.delete_cookie("Session_id", path="/")
    return {"success": True, "message": "변경 완료"}
