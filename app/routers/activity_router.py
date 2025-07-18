from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.activity import Activity
from app.models.user import User
from app.schemas import (
    ActivityCreate, ActivityUpdate, ActivityReadBasic, ActivityReadDetail
)
from app.core.security import get_current_user
from typing import List, Optional
from datetime import datetime

router = APIRouter(prefix="/activities", tags=["activities"])

# MET lookup table (type, intensity) -> MET value
def get_met_value(activity_type: str, intensity: Optional[str]) -> float:
    met_table = {
        ("walking", "low"): 2.5,
        ("walking", "moderate"): 3.5,
        ("walking", "high"): 4.5,
        ("running", "low"): 7.0,
        ("running", "moderate"): 9.8,
        ("running", "high"): 11.0,
        ("cycling", "low"): 4.0,
        ("cycling", "moderate"): 6.8,
        ("cycling", "high"): 8.0,
    }
    return met_table.get((activity_type.lower(), (intensity or "moderate").lower()), 3.0)

# Calories burned calculation
def calculate_calories_burned(met: float, weight_kg: float, duration_min: Optional[int]) -> float:
    if not duration_min:
        return 0.0
    duration_hr = duration_min / 60.0
    return round(met * weight_kg * duration_hr, 2)

# Permissions: admin or owner
def can_edit_activity(activity: Activity, user: User) -> bool:
    return activity.user_id == user.id or user.is_admin

@router.post("/", response_model=ActivityReadDetail, status_code=status.HTTP_201_CREATED)
def create_activity(activity_in: ActivityCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    weight_kg = current_user.weight if current_user.weight else 70.0
    met = get_met_value(activity_in.type, activity_in.intensity)
    calories = calculate_calories_burned(met, weight_kg, activity_in.duration_min)
    assert current_user.id is not None, "User ID must not be None"
    activity = Activity(
        user_id=int(current_user.id),
        type=activity_in.type,
        intensity=activity_in.intensity,
        duration_min=activity_in.duration_min,
        timestamp=activity_in.timestamp or datetime.utcnow(),
        note=activity_in.note,
        calories_burned=calories
    )
    session.add(activity)
    session.commit()
    session.refresh(activity)
    return ActivityReadDetail.from_orm(activity)

@router.get("/", response_model=List[ActivityReadBasic])
def list_activities(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    if current_user.is_admin:
        activities = session.exec(select(Activity)).all()
    else:
        activities = session.exec(select(Activity).where(Activity.user_id == current_user.id)).all()
    return [ActivityReadBasic.from_orm(a) for a in activities]

@router.get("/{activity_id}", response_model=ActivityReadDetail)
def get_activity(activity_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not can_edit_activity(activity, current_user) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return ActivityReadDetail.from_orm(activity)

@router.put("/{activity_id}", response_model=ActivityReadDetail)
def update_activity(activity_id: int, activity_in: ActivityUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not can_edit_activity(activity, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    # Update fields
    for field, value in activity_in.dict(exclude_unset=True).items():
        setattr(activity, field, value)
    # Recalculate calories if relevant fields changed
    weight_kg = current_user.weight if current_user.weight else 70.0
    met = get_met_value(activity.type, activity.intensity)
    activity.calories_burned = calculate_calories_burned(met, weight_kg, activity.duration_min)
    session.commit()
    session.refresh(activity)
    return ActivityReadDetail.from_orm(activity)

@router.delete("/{activity_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_activity(activity_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    activity = session.get(Activity, activity_id)
    if not activity:
        raise HTTPException(status_code=404, detail="Activity not found")
    if not can_edit_activity(activity, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    session.delete(activity)
    session.commit()
    return None 