from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session
from auth.auth_session import get_current_user
from auth.auth_session import delete_session
from auth.auth_session import request_session_id
from database.connection import Create_db
from models.users import Users
from models.notification import Push_Token
from sqlalchemy import delete
#--------------------------------------------------

#라우터 선언
router_logout = APIRouter()

#로그아웃 함수
@router_logout.post("/api/v1/logout")
def logout(request: Request, response: Response, session_id: Users = Depends(get_current_user), db: Session = Depends(Create_db)):
    if session_id is not None:
        db.execute(delete(Push_Token).where(Push_Token.session_id == request_session_id(request)))
        delete_session(
            request_session_id(request),
            db
        )

    response.delete_cookie(
        key="session_id",
        path="/"
    )
    response.delete_cookie(key="Session_id", path="/")

    return {
        "message": "로그아웃되었습니다."
    }
