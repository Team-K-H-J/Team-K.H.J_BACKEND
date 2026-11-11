from io import BytesIO
import os
import warnings

from fastapi import APIRouter, Depends, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageOps, UnidentifiedImageError
from pwdlib import PasswordHash
from sqlalchemy import delete, update
from sqlalchemy.orm import Session

from auth.auth_admin import is_admin
from auth.auth_session import get_current_user
from config import BASE_DIR
from database.connection import Create_db
from models.account import Email_Verification, Login_Attempt, User_Profile, User_Settings
from models.favorite import Favorite
from models.inquiry import Inquiry
from models.notice import Notice
from models.notification import Notification, Push_Token
from models.operations import Cycle_User
from models.session_model import Session_Model
from models.subscribe import Subscribe
from models.subscribe_log import Subscribe_log
from models.users import Users
from Schemas.application import ProfilePatch, SettingsPatch
from Schemas.auth_password import password_schema
from services.common import uid

router_account = APIRouter()
password_hashing = PasswordHash.recommended()
UPLOADS = BASE_DIR / ".local" / "profile-images"


def profile_view(user, db):
    profile = db.get(User_Profile, user.user_id)
    return {"user_id": uid(user.user_id), "email": user.email, "name": user.name,
            "number": user.number, "image_url": profile.image_url if profile else None,
            "is_admin": is_admin(user)}


@router_account.get("/api/v1/users/me")
def profile(db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    return profile_view(user, db)


@router_account.patch("/api/v1/users/me")
def update_profile(data: ProfilePatch, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    if data.name is not None:
        user.name = data.name
    if data.number is not None:
        user.number = data.number
    if "image_url" in data.model_fields_set:
        row = db.get(User_Profile, user.user_id)
        if row is None:
            row = User_Profile(user_id=user.user_id)
            db.add(row)
        row.image_url = str(data.image_url) if data.image_url else None
    db.commit()
    return profile_view(user, db)


@router_account.put("/api/v1/users/me/image")
async def upload_image(file: UploadFile, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "프로필 이미지는 5MB 이하여야 합니다.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(BytesIO(raw)) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise HTTPException(422, "JPEG, PNG, WEBP 이미지만 사용할 수 있습니다.")
                if image.width * image.height > 10_000_000:
                    raise HTTPException(413, "이미지 해상도가 너무 큽니다.")
                image = ImageOps.exif_transpose(image).convert("RGBA")
                image.thumbnail((1024, 1024))
                output = BytesIO()
                image.save(output, format="PNG")
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, "올바른 이미지 파일이 아닙니다.") from None
    UPLOADS.mkdir(parents=True, exist_ok=True)
    target = UPLOADS / (uid(user.user_id) + ".png")
    temporary = target.with_suffix(".tmp")
    temporary.write_bytes(output.getvalue())
    os.replace(temporary, target)
    row = db.get(User_Profile, user.user_id)
    if row is None:
        row = User_Profile(user_id=user.user_id)
        db.add(row)
    row.image_url = "/api/v1/users/me/image"
    db.commit()
    return profile_view(user, db)


@router_account.get("/api/v1/users/me/image")
def profile_image(db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    row = db.get(User_Profile, user.user_id)
    target = UPLOADS / (uid(user.user_id) + ".png")
    if row is None or row.image_url != "/api/v1/users/me/image" or not target.is_file():
        raise HTTPException(404, "프로필 이미지가 없습니다.")
    return FileResponse(target, media_type="image/png", headers={"Cache-Control": "private, no-cache", "X-Content-Type-Options": "nosniff"})


def settings_view(row):
    names = ("notifications_enabled", "vibration_enabled", "theme", "completed", "paused", "stopped")
    return {name: getattr(row, name) for name in names}


def settings_for(db, user):
    row = db.get(User_Settings, user.user_id)
    if row is None:
        row = User_Settings(user_id=user.user_id)
        db.add(row)
        db.flush()
    return row


@router_account.get("/api/v1/users/me/settings")
def settings(db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    row = settings_for(db, user)
    db.commit()
    return settings_view(row)


@router_account.patch("/api/v1/users/me/settings")
def update_settings(data: SettingsPatch, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    row = settings_for(db, user)
    for name, value in data.model_dump(exclude_none=True).items():
        setattr(row, name, value)
    db.commit()
    return settings_view(row)


@router_account.delete("/api/v1/users/me")
def delete_account(data: password_schema, response: Response, db: Session = Depends(Create_db),
                   user: Users = Depends(get_current_user)):
    if not password_hashing.verify(data.password, user.password_hash):
        raise HTTPException(403, "비밀번호가 일치하지 않습니다.")
    user_id, email = user.user_id, user.email
    for model in (Notification, Push_Token, Inquiry, Cycle_User, User_Profile, User_Settings,
                  Subscribe_log, Subscribe, Favorite, Session_Model):
        db.execute(delete(model).where(model.user_id == user_id))
    db.execute(update(Notice).where(Notice.author_id == user_id).values(author_id=None))
    db.execute(delete(Email_Verification).where(Email_Verification.email == email))
    db.execute(delete(Login_Attempt).where(Login_Attempt.email == email))
    db.delete(user)
    db.commit()
    (UPLOADS / (uid(user_id) + ".png")).unlink(missing_ok=True)
    response.delete_cookie("session_id", path="/")
    response.delete_cookie("Session_id", path="/")
    return {"success": True, "message": "회원탈퇴가 완료되었습니다."}

