from fastapi import Depends, HTTPException
from auth.auth_session import get_current_user
from config import admin_emails
from models.users import Users


def is_admin(user: Users) -> bool:
    return user.email.lower() in admin_emails()


def get_admin(user: Users = Depends(get_current_user)) -> Users:
    if not is_admin(user):
        raise HTTPException(status_code=403, detail="관리자 권한이 필요합니다.")
    return user
