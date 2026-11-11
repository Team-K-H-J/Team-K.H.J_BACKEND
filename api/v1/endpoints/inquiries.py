from uuid import UUID
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.auth_admin import get_admin
from auth.auth_session import get_current_user
from database.connection import Create_db
from models.devices import Devices
from models.inquiry import Inquiry
from models.users import Users
from Schemas.application import InquiryCreate, InquiryStatus
from services.common import iso, uid, utcnow

router_inquiries = APIRouter()


def inquiry_view(row, db=None):
    result = {"id": uid(row.id), "device_id": row.device_id, "error_type": row.error_type, "title": row.title,
              "content": row.content, "status": row.status, "created_at": iso(row.created_at), "updated_at": iso(row.updated_at)}
    if db is not None:
        user = db.get(Users, row.user_id)
        result["reporter"] = {"user_id": uid(user.user_id), "name": user.name, "number": user.number} if user else None
    return result


@router_inquiries.post("/api/v1/inquiries")
def create_inquiry(data: InquiryCreate, db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    if data.device_id and db.get(Devices, data.device_id) is None:
        raise HTTPException(404, "장치가 존재하지 않습니다.")
    now = utcnow()
    values = data.model_dump()
    values["title"] = data.title or data.error_type
    row = Inquiry(**values, user_id=user.user_id, status="unread", created_at=now, updated_at=now)
    db.add(row)
    db.commit()
    return inquiry_view(row)


@router_inquiries.get("/api/v1/inquiries")
def my_inquiries(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                 db: Session = Depends(Create_db), user: Users = Depends(get_current_user)):
    return [inquiry_view(row) for row in db.scalars(select(Inquiry).where(Inquiry.user_id == user.user_id)
            .order_by(Inquiry.created_at.desc(), Inquiry.id.desc()).offset(offset).limit(limit))]


@router_inquiries.get("/api/v1/admin/inquiries", dependencies=[Depends(get_admin)])
def admin_inquiries(status: Literal["unread", "reviewing", "resolved"] | None = None,
                    device_id: str | None = None, limit: int = Query(50, ge=1, le=100),
                    offset: int = Query(0, ge=0), db: Session = Depends(Create_db)):
    query = select(Inquiry)
    if status:
        query = query.where(Inquiry.status == status)
    if device_id:
        query = query.where(Inquiry.device_id == device_id)
    return [inquiry_view(row, db) for row in db.scalars(query.order_by(Inquiry.created_at.desc(), Inquiry.id.desc()).offset(offset).limit(limit))]


@router_inquiries.get("/api/v1/admin/inquiries/{inquiry_id}", dependencies=[Depends(get_admin)])
def admin_detail(inquiry_id: UUID, db: Session = Depends(Create_db)):
    row = db.get(Inquiry, inquiry_id.bytes)
    if row is None:
        raise HTTPException(404, "문의가 존재하지 않습니다.")
    return inquiry_view(row, db)


@router_inquiries.patch("/api/v1/admin/inquiries/{inquiry_id}/status", dependencies=[Depends(get_admin)])
def change_inquiry_status(inquiry_id: UUID, data: InquiryStatus, db: Session = Depends(Create_db)):
    row = db.get(Inquiry, inquiry_id.bytes)
    if row is None:
        raise HTTPException(404, "문의가 존재하지 않습니다.")
    row.status, row.updated_at = data.status, utcnow()
    db.commit()
    return inquiry_view(row, db)

