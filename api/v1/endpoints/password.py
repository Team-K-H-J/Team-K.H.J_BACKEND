from fastapi import APIRouter,Depends , Response,HTTPException
from Schemas.forget_password import password_forget
from sqlalchemy.orm import Session
from database.connection import Create_db
from models.users import Users
from auth.auth_email import make_and_send_email_number, check_email_number
from auth.auth_session import create_session
from Schemas.email_code_schema import email_code_schema
from auth.auth_session import get_current_user
from pwdlib import PasswordHash
from Schemas.auth_password import password_schema
#-----------------------------

#라우터 선언
router_password = APIRouter()

#혜시 객체 생성
password_hashing = PasswordHash.recommended()

#학년, 반, 번호, 이름, 이메일 인증
@router_password.post("/api/v1/forget/password")
def forget_password(user_data: password_forget,db: Session = Depends(Create_db)):

    #사용자 객체 불러오기
    user = db.get(
        Users,
        user_data.email
    )
    
    #학번 검증
    if user.email is not user_data.email | user.number is not user_data.number | user.name is not user_data.name:
        return{
            "success":False,
            "message":"입력한 사용자 정보가 일치하지 않습니다."
        }

    #이메일 인증 번호 발송
    result = make_and_send_email_number(user_data.email)

    return result

#이메일 인증번호 확인
@router_password.post("/api/v1/forget/check/email_code")
def forget_check_email_code( response : Response, user_code: email_code_schema,db: Session = Depends(Create_db)):

    #인증 번호 확인
    result = check_email_number(user_code)

    if result["success"] is False:
        return result

    else:

        #사용자 id 객체 생성
        user = db.get(Users, user_code.email)

        #임의의 세션 생성
        create_session(user, response,db)

    return result

#비밀 번호 변경 인증
@router_password.post("/api/v1/change/password_auth")
def auth_password_change(user_know: password_schema, user_data: Users = Depends(get_current_user)):
    #일치하는지 검증
    if password_hashing.verify(user_know.password, user_data.password_hash) is not True:
        return {
            "success":False,
            "message": "비밀번호가 일치하지 않습니다."
        }

    return {
        "success":True,
        "message": "비밀번호가 일치함"
    }


#비밀 번호 변경
@router_password.post("/api/v1/change/password")
def change_password(user_want : password_schema, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):

    #비번 해싱
    hashed = password_hashing.hash(user_want.password)

    #비번 변경
    user.password_hash = hashed

    #변경 사항 저장
    db.commit()

    return {
        "success":True,
        "message": "변경 완료"
    }