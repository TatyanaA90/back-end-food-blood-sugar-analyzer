from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.condition_log import ConditionLog
from app.models.user import User
from app.schemas import (
    ConditionLogCreate, ConditionLogUpdate, ConditionLogReadBasic, ConditionLogReadDetail
)
from app.core.security import get_current_user
from typing import List
from datetime import datetime

router = APIRouter(prefix="/condition-logs", tags=["condition-logs"])

# Permissions: admin or owner
def can_edit_condition_log(log: ConditionLog, user: User) -> bool:
    return log.user_id == user.id or user.is_admin

@router.post("/", response_model=ConditionLogReadDetail, status_code=status.HTTP_201_CREATED)
def create_condition_log(log_in: ConditionLogCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    assert current_user.id is not None, "User ID must not be None"
    log = ConditionLog(
        user_id=int(current_user.id),
        type=log_in.type,
        value=log_in.value,
        timestamp=log_in.timestamp or datetime.utcnow(),
        note=log_in.note
    )
    session.add(log)
    session.commit()
    session.refresh(log)
    return ConditionLogReadDetail.from_orm(log)

@router.get("/", response_model=List[ConditionLogReadBasic])
def list_condition_logs(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        logs = session.exec(select(ConditionLog)).all()
    else:
        logs = session.exec(select(ConditionLog).where(ConditionLog.user_id == current_user.id)).all()
    return [ConditionLogReadBasic.from_orm(l) for l in logs]

@router.get("/{log_id}", response_model=ConditionLogReadDetail)
def get_condition_log(log_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    log = session.get(ConditionLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="ConditionLog not found")
    if not can_edit_condition_log(log, current_user) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return ConditionLogReadDetail.from_orm(log)

@router.put("/{log_id}", response_model=ConditionLogReadDetail)
def update_condition_log(log_id: int, log_in: ConditionLogUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    log = session.get(ConditionLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="ConditionLog not found")
    if not can_edit_condition_log(log, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    for field, value in log_in.dict(exclude_unset=True).items():
        setattr(log, field, value)
    session.commit()
    session.refresh(log)
    return ConditionLogReadDetail.from_orm(log)

@router.delete("/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_condition_log(log_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    log = session.get(ConditionLog, log_id)
    if not log:
        raise HTTPException(status_code=404, detail="ConditionLog not found")
    if not can_edit_condition_log(log, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    session.delete(log)
    session.commit()
    return None
