from fastapi import APIRouter,Depends,HTTPException
from auth.auth_email import make_and_send_email_number, check_email_number
from Schemas.auth_email_schema import auth_email_schema
from sqlalchemy.orm import Session
from sqlalchemy import select
from database.connection import Create_db
from models.users import Users
from Schemas.email_code_schema import email_code_schema
from pathlib import Path
from dotenv import load_dotenv
import os

#-----------------------------

# 프로젝트 최상위 폴더 경로
BASE_DIR = Path(__file__).resolve().parent.parent

#.env 파일 읽기
load_dotenv(BASE_DIR / ".env")

# .env에서 발송 메일 정보 가져오기
sender_email = os.getenv("GMAIL_ADDRESS")
password = os.getenv("GMAIL_APP_PASSWORD")

#라우터 연결
router_email = APIRouter()

#인증 번호 저장 변수 선언
contify_code = {}

#회원 가입 이메일 인증 번호 발송 함수
@router_email.post("/api/v1/signup/email")
def signup_email_contify(user_email:auth_email_schema, db:Session = Depends(Create_db)):

    #이메일 중복 검사
    exist_user = db.scalar(
        select(Users).where(Users.email == user_email.email)
    )
    
    if exist_user is not None:
        raise HTTPException(
            status_code = 409,
            detail = "이미 사용중인 이메일입니다."
        )

    make_and_send_email_number(user_email, db)

    return {
        "success":True
    }


#이메일 인증 번호 검증 함수
@router_email.post("/api/v1/check/email_code")
def email_code_check(user_code:email_code_schema, db: Session = Depends(Create_db)):

    #인증 검중 함수 호출
    result = check_email_number(user_code, db)

    if result["success"] is False:
        return result

    return {
        "success":True,
        "massage":"인증 성공"
    }
