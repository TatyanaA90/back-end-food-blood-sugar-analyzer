from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.glucose_reading import GlucoseReading
from app.core.security import get_current_user
from app.models.user import User
from typing import Optional
from datetime import datetime, date
import statistics

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/glucose-summary")
def glucose_summary(
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    low: float = Query(70, description="Low threshold for in-target percent"),
    high: float = Query(180, description="High threshold for in-target percent"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Build query for current user's glucose readings
    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start_date:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end_date, datetime.max.time()))
    readings = session.exec(query).all()
    values = [r.value for r in readings if r.value is not None]
    num_readings = len(values)
    if num_readings == 0:
        return {
            "average": None,
            "min": None,
            "max": None,
            "std_dev": None,
            "num_readings": 0,
            "in_target_percent": None
        }
    average = sum(values) / num_readings
    min_val = min(values)
    max_val = max(values)
    std_dev = statistics.stdev(values) if num_readings > 1 else 0.0
    in_target = [v for v in values if low <= v <= high]
    in_target_percent = (len(in_target) / num_readings) * 100
    return {
        "average": average,
        "min": min_val,
        "max": max_val,
        "std_dev": std_dev,
        "num_readings": num_readings,
        "in_target_percent": in_target_percent
    }
