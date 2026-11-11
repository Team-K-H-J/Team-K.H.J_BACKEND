import hashlib
import hmac
import os
import secrets
import smtplib
import ssl
from datetime import timedelta
from email.message import EmailMessage

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

import config  # noqa: F401 -- register models or load environment
from models.account import Email_Verification
from services.common import utcnow


def code_digest(email: str, purpose: str, code: str) -> str:
    secret = os.getenv("EMAIL_CODE_SECRET")
    if not secret:
        raise HTTPException(503, "이메일 인증 설정이 필요합니다.")
    return hmac.new(secret.encode(), f"{email}:{purpose}:{code}".encode(), hashlib.sha256).hexdigest()


def make_and_send_email_number(user_email, db: Session, purpose: str = "signup"):
    email = str(getattr(user_email, "email", user_email)).lower()
    now = utcnow()
    if db.get(Email_Verification, (email, purpose)) is None:
        try:
            with db.begin_nested():
                db.add(Email_Verification(email=email, purpose=purpose, code_hash="0" * 64,
                       expires_at=now, sent_at=now - timedelta(days=1), attempts=0))
                db.flush()
        except IntegrityError:
            # Another worker completed the first request while we waited.
            pass
    record = db.scalar(select(Email_Verification).where(
        Email_Verification.email == email, Email_Verification.purpose == purpose)
        .with_for_update().execution_options(populate_existing=True))
    if record and (now - record.sent_at).total_seconds() < 30:
        raise HTTPException(429, "인증번호는 30초 후 다시 요청해 주세요.")
    code = f"{secrets.randbelow(1_000_000):06d}"
    digest = code_digest(email, purpose, code)
    sender = os.getenv("GMAIL_ADDRESS")
    password = os.getenv("GMAIL_APP_PASSWORD")
    if not sender or not password:
        raise HTTPException(503, "메일 발송 설정이 필요합니다.")
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = sender, email, "J.H.Y-이메일 인증번호"
    message.set_content("인증 번호는 " + code + " 입니다.")
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context(), timeout=10) as smtp:
            smtp.login(sender, password)
            smtp.send_message(message)
    except (smtplib.SMTPException, OSError):
        db.rollback()
        raise HTTPException(503, "메일을 발송하지 못했습니다. 잠시 후 다시 시도해 주세요.") from None
    if record is None:
        record = Email_Verification(email=email, purpose=purpose)
        db.add(record)
    record.code_hash, record.sent_at = digest, now
    record.expires_at = now + timedelta(minutes=5)
    record.attempts, record.verified_at = 0, None
    db.commit()
    return {"success": True, "message": "메일 발송 성공"}


def check_email_number(user_code, db: Session, purpose: str = "signup"):
    email = str(user_code.email).lower()
    record = db.scalar(select(Email_Verification).where(
        Email_Verification.email == email, Email_Verification.purpose == purpose).with_for_update())
    if record is None:
        return {"success": False, "massage": "이메일이 옳지 않습니다."}
    if utcnow() >= record.expires_at:
        db.delete(record)
        db.commit()
        return {"success": False, "massage": "시간 초과"}
    if record.attempts >= 5 or record.verified_at is not None:
        return {"success": False, "massage": "인증 실패"}
    record.attempts += 1
    valid = hmac.compare_digest(record.code_hash, code_digest(email, purpose, user_code.code))
    if valid:
        record.verified_at = utcnow()
    db.commit()
    return {"success": valid, "massage": "인증 성공" if valid else "인증 실패"}
