from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.glucose_reading import GlucoseReading
from app.core.security import get_current_user
from app.models.user import User
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
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

@router.get("/glucose-trend")
def glucose_trend(
    # window: lets users select a standard time period (day, week, month, etc.) for their data
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    # moving_avg: smooths out short-term spikes to show the overall trend. 
    # This helps you see the “big picture” rather than getting distracted by every little up and down.
    moving_avg: Optional[int] = Query(None, description="Window size for moving average (in readings)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns timestamped glucose readings for the selected timeframe, ready for line chart visualization.
    Supports optional moving average.
    """
    # Determine date range based on window
    now = datetime.utcnow()
    if window == "day":
        start = now.date()
        end = now.date()
    elif window == "week":
        start = (now - timedelta(days=6)).date()
        end = now.date()
    elif window == "month":
        start = (now - timedelta(days=29)).date()
        end = now.date()
    elif window == "3months":
        start = (now - timedelta(days=89)).date()
        end = now.date()
    elif window == "custom":
        if not start_date or not end_date:
            raise HTTPException(status_code=400, detail="For custom window, start_date and end_date are required.")
        start = start_date
        end = end_date
    else:
        # Default: all available data
        start = start_date
        end = end_date

    # Build query for current user's glucose readings in the date range
    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    readings = session.exec(query).all()
    readings = sorted(readings, key=lambda r: r.timestamp)

    readings_list = [
        {
            "timestamp": r.timestamp.isoformat(),
            "value": r.value,
            "unit": r.unit
        }
        for r in readings if r.value is not None and r.timestamp is not None
    ]

    # Calculate moving average if requested
    moving_avg_list = []
    if moving_avg and moving_avg > 1 and len(readings_list) >= moving_avg:
        values = [r["value"] for r in readings_list]
        for i in range(moving_avg - 1, len(values)):
            avg = sum(values[i - moving_avg + 1:i + 1]) / moving_avg
            moving_avg_list.append({
                "timestamp": readings_list[i]["timestamp"],
                "value": avg
            })

    meta = {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "num_readings": len(readings_list),
        "unit": readings_list[0]["unit"] if readings_list else "mg/dl"
    }

    result = {
        "readings": readings_list,
        "meta": meta
    }
    if moving_avg_list:
        result["moving_average"] = moving_avg_list
    return result
