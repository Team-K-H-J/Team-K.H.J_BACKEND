#----------모듈 불러오기----------
from fastapi import Depends, APIRouter, HTTPException
from database.connection import Create_db
from sqlalchemy import select
from sqlalchemy.orm import Session

#파일 연결
from models.state import State
#----------라우터 연결----------
router_load_state = APIRouter()


#건조기 테이블 조회
@router_load_state.get("/api/v1/state/all")
def get_states(db: Session = Depends(Create_db)):
    stmt = select(State)
    state = db.scalars(stmt).all()

    return state

#개별 건조기 테이블 조회
@router_load_state.get("/api/v1/state/{device_id}")
def get_state(device_id: str, db: Session = Depends(Create_db)):
    stmt = select(State).where(State.device_id == device_id)
    state = db.scalar(stmt)
    if state is None:
        raise HTTPException(404, "장치 상태가 존재하지 않습니다.")

    return state
