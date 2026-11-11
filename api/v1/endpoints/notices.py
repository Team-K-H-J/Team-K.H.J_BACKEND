from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from auth.auth_admin import get_admin
from database.connection import Create_db
from models.notice import Notice
from models.users import Users
from Schemas.application import NoticeCreate, NoticePatch
from services.common import iso, uid, utcnow

router_notices = APIRouter()


def notice_view(row):
    return {"id": uid(row.id), "title": row.title, "content": row.content, "pinned": row.pinned,
            "created_at": iso(row.created_at), "updated_at": iso(row.updated_at)}


@router_notices.get("/api/v1/admin/notices", dependencies=[Depends(get_admin)])
@router_notices.get("/api/v1/notices")
def notices(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(Create_db)):
    return [notice_view(row) for row in db.scalars(select(Notice).order_by(
        Notice.pinned.desc(), Notice.created_at.desc(), Notice.id.desc()).offset(offset).limit(limit))]


@router_notices.get("/api/v1/notices/{notice_id}")
def notice_detail(notice_id: UUID, db: Session = Depends(Create_db)):
    row = db.get(Notice, notice_id.bytes)
    if row is None:
        raise HTTPException(404, "공지사항이 존재하지 않습니다.")
    return notice_view(row)


@router_notices.post("/api/v1/admin/notices")
def create_notice(data: NoticeCreate, db: Session = Depends(Create_db), admin: Users = Depends(get_admin)):
    now = utcnow()
    row = Notice(**data.model_dump(), author_id=admin.user_id, created_at=now, updated_at=now)
    db.add(row)
    db.commit()
    return notice_view(row)


@router_notices.patch("/api/v1/admin/notices/{notice_id}")
def edit_notice(notice_id: UUID, data: NoticePatch, db: Session = Depends(Create_db), admin: Users = Depends(get_admin)):
    row = db.get(Notice, notice_id.bytes)
    if row is None:
        raise HTTPException(404, "공지사항이 존재하지 않습니다.")
    for name, value in data.model_dump(exclude_none=True).items():
        setattr(row, name, value)
    row.updated_at = utcnow()
    db.commit()
    return notice_view(row)


@router_notices.delete("/api/v1/admin/notices/{notice_id}", dependencies=[Depends(get_admin)])
def delete_notice(notice_id: UUID, db: Session = Depends(Create_db)):
    row = db.get(Notice, notice_id.bytes)
    if row is None:
        raise HTTPException(404, "공지사항이 존재하지 않습니다.")
    db.delete(row)
    db.commit()
    return {"success": True}

