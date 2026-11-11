from fastapi import HTTPException, Depends, APIRouter
from sqlalchemy.orm import Session
from sqlalchemy import select
from pwdlib import PasswordHash
from database.connection import Create_db
from Schemas.signup_schema import SignupData
from models.users import Users
from models.account import Email_Verification
from services.common import utcnow
from sqlalchemy.exc import IntegrityError

#--------------------------------

#라우터 연결
router_signup = APIRouter()

#혜시 객체 생성
password_hashing = PasswordHash.recommended()

#회원가입 API
@router_signup.post("/api/v1/users/signup")
def signup(User_data: SignupData, db: Session = Depends(Create_db)):

    #이메일 중복 검사
    exist_user = db.scalar(
        select(Users).where(Users.email == User_data.email)
    )

    if exist_user is not None:
        raise HTTPException(
            status_code = 409,
            detail = "이미 사용중인 이메일입니다."
        )

    email = str(User_data.email).lower()
    verification = db.scalar(select(Email_Verification).where(
        Email_Verification.email == email,
        Email_Verification.purpose == "signup"
    ).with_for_update())
    if verification is None or verification.verified_at is None or verification.expires_at <= utcnow():
        raise HTTPException(403, "이메일 인증을 먼저 완료해 주세요.")

    #비번 해싱
    hashed = password_hashing.hash(User_data.password)

    #User 객체 생성
    new_user = Users(
        email = email,
        password_hash = hashed,
        name = User_data.name,
        number = User_data.number
    )

    #User 객체 저장
    db.add(new_user)
    db.delete(verification)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(409, "이미 사용중인 이메일입니다.") from None

    return{
		 "success": True,
		 "message": "회원가입이 완료되었습니다."
    }
