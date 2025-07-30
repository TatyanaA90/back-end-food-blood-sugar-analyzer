from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.core.security import get_current_user
from app.models.user import User
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta, UTC
import statistics
from collections import defaultdict
import math

router = APIRouter(prefix="/analytics", tags=["analytics"])

@router.get("/glucose-summary")
def glucose_summary(
    group_by: Optional[str] = Query(None, description="Group by 'day', 'week', or 'month'. If not set, returns a summary for the whole range."),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    low: float = Query(70, description="Low threshold for in-target percent"),
    high: float = Query(180, description="High threshold for in-target percent"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Returns a summary of glucose readings for the selected date range.
    - If group_by is None, returns a single summary for the whole range.
    - If group_by is 'day', 'week', or 'month', returns a list of summaries for each period.
    """

    # Build query for current user's glucose readings
    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start_date:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start_date, datetime.min.time()))
    if end_date:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end_date, datetime.max.time()))
    readings = session.exec(query).all()
    readings = [r for r in readings if r.value is not None and r.timestamp is not None]

    if not group_by:
        # Whole-range summary
        values = [r.value for r in readings]
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
    else:
        # Grouped summary
        summary = []
        groups = defaultdict(list)
        for r in readings:
            ts = r.timestamp
            if group_by == "day":
                key = ts.date().isoformat()
            elif group_by == "week":
                # ISO week: (year, week number)
                key = f"{ts.isocalendar().year}-W{ts.isocalendar().week:02d}"
            elif group_by == "month":
                key = f"{ts.year}-{ts.month:02d}"
            else:
                raise HTTPException(status_code=400, detail="group_by must be 'day', 'week', or 'month'")
            groups[key].append(r.value)
        for period in sorted(groups.keys()):
            values = groups[period]
            num_readings = len(values)
            if num_readings == 0:
                continue
            average = sum(values) / num_readings
            min_val = min(values)
            max_val = max(values)
            std_dev = statistics.stdev(values) if num_readings > 1 else 0.0
            in_target = [v for v in values if low <= v <= high]
            in_target_percent = (len(in_target) / num_readings) * 100
            summary.append({
                "period": period,
                "average": average,
                "min": min_val,
                "max": max_val,
                "std_dev": std_dev,
                "in_target_percent": in_target_percent,
                "num_readings": num_readings
            })
        return {
            "summary": summary,
            "meta": {
                "group_by": group_by,
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None
            }
        }

# /glucose-summary-by-period will provide grouped summaries (by day, week, or month) for visualization and trend analysis.

@router.get("/glucose-trend")
def glucose_trend(
    # window: lets users select a standard time period (day, week, month, etc.) for their data
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    # moving_avg: smooths out short-term spikes to show the overall trend. 
    # This helps to see the "big picture" rather than getting distracted by every little up and down.
    moving_avg: Optional[int] = Query(None, description="Window size for moving average (in readings)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns timestamped glucose readings for the selected timeframe, ready for line chart visualization.
    Supports optional moving average.
    """
    # Determine date range based on window
    now = datetime.now(UTC)
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

@router.get("/agp-overlay")
def agp_overlay(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    interval_minutes: int = Query(30, description="Time bin size in minutes (default 30)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns glucose values overlaid by time of day for AGP plot, including median, p25, p75, min, max, and num_readings for each time slot.
    """
    now = datetime.now(UTC)
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
        start = start_date
        end = end_date

    # Query all glucose readings for the user in the date range
    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    readings = session.exec(query).all()

    # Bin readings by time of day (e.g., every 30 minutes)
    bins = {}  # key: minutes since midnight, value: list of glucose values
    for r in readings:
        if r.timestamp is None or r.value is None:
            continue
        t = r.timestamp.time()
        minutes = t.hour * 60 + t.minute
        bin_start = (minutes // interval_minutes) * interval_minutes
        if bin_start not in bins:
            bins[bin_start] = []
        bins[bin_start].append(r.value)

    # Prepare AGP stats for each bin
    agp = []
    for bin_start in sorted(bins.keys()):
        values = sorted(bins[bin_start])
        n = len(values)
        if n == 0:
            continue
        median = statistics.median(values)
        p25 = statistics.quantiles(values, n=4)[0] if n >= 4 else values[0]
        p75 = statistics.quantiles(values, n=4)[2] if n >= 4 else values[-1]
        min_val = min(values)
        max_val = max(values)
        # Format time as HH:MM
        hours = bin_start // 60
        minutes = bin_start % 60
        time_of_day = f"{hours:02d}:{minutes:02d}"
        agp.append({
            "time_of_day": time_of_day,
            "median": median,
            "p25": p25,
            "p75": p75,
            "min": min_val,
            "max": max_val,
            "num_readings": n
        })

    meta = {
        "interval_minutes": interval_minutes,
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None
    }

    return {"agp": agp, "meta": meta}

@router.get("/time-in-range")
def time_in_range(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    very_low_threshold: float = Query(54, description="Very low glucose threshold (mg/dl)"),
    low_threshold: float = Query(70, description="Low glucose threshold (mg/dl)"),
    target_low: float = Query(70, description="Target range low threshold (mg/dl)"),
    target_high: float = Query(180, description="Target range high threshold (mg/dl)"),
    high_threshold: float = Query(250, description="High glucose threshold (mg/dl)"),
    very_high_threshold: float = Query(400, description="Very high glucose threshold (mg/dl)"),
    unit: str = Query("mg/dl", description="Unit for thresholds: 'mg/dl' or 'mmol/l'"),
    show_percentage: bool = Query(True, description="Show results as percentages (True) or absolute values (False)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns percentage of time spent in different glucose ranges for the selected period.
    Useful for pie charts and stacked bar visualizations.
    """
    now = datetime.now(UTC)
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
        start = start_date
        end = end_date

    # Query all glucose readings for the user in the date range
    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    readings = session.exec(query).all()
    
    # Filter valid readings
    valid_readings = [r for r in readings if r.value is not None and r.timestamp is not None]
    
    if not valid_readings:
        return {
            "time_in_range": {
                "very_low": 0.0,
                "low": 0.0,
                "in_range": 0.0,
                "high": 0.0,
                "very_high": 0.0
            },
            "total_readings": 0,
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "very_low_threshold": very_low_threshold,
                "low_threshold": low_threshold,
                "target_low": target_low,
                "target_high": target_high,
                "high_threshold": high_threshold,
                "very_high_threshold": very_high_threshold,
                "unit": unit
            }
        }

    # Count readings in each range
    very_low_count = 0
    low_count = 0
    in_range_count = 0
    high_count = 0
    very_high_count = 0
    
    for reading in valid_readings:
        value = reading.value
        if value < very_low_threshold:
            very_low_count += 1
        elif very_low_threshold <= value < low_threshold:
            low_count += 1
        elif target_low <= value <= target_high:
            in_range_count += 1
        elif target_high < value <= high_threshold:
            high_count += 1
        else:  # value > high_threshold
            very_high_count += 1
    
    total_readings = len(valid_readings)
    
    # Calculate percentages or absolute values based on show_percentage parameter
    if show_percentage:
        time_in_range_data = {
            "very_low": round((very_low_count / total_readings) * 100, 2),
            "low": round((low_count / total_readings) * 100, 2),
            "in_range": round((in_range_count / total_readings) * 100, 2),
            "high": round((high_count / total_readings) * 100, 2),
            "very_high": round((very_high_count / total_readings) * 100, 2)
        }
    else:
        time_in_range_data = {
            "very_low": very_low_count,
            "low": low_count,
            "in_range": in_range_count,
            "high": high_count,
            "very_high": very_high_count
        }
    
    # Add raw counts for additional context
    counts = {
        "very_low": very_low_count,
        "low": low_count,
        "in_range": in_range_count,
        "high": high_count,
        "very_high": very_high_count
    }
    
    meta = {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "very_low_threshold": very_low_threshold,
        "low_threshold": low_threshold,
        "target_low": target_low,
        "target_high": target_high,
        "high_threshold": high_threshold,
        "very_high_threshold": very_high_threshold,
        "unit": unit,
        "show_percentage": show_percentage,
        "total_readings": total_readings
    }
    
    return {
        "time_in_range": time_in_range_data,
        "counts": counts,
        "meta": meta
    }

@router.get("/glucose-variability")
def glucose_variability(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    include_explanations: bool = Query(True, description="Include plain-language explanations for each metric"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns glucose variability metrics (SD, CV, GMI) for the selected timeframe.
    Includes plain-language explanations for clinical interpretation.
    """
    # Determine date range based on window
    now = datetime.now(UTC)
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
        start = start_date
        end = end_date

    # Query glucose readings for the user in the date range
    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    readings = session.exec(query).all()
    
    # Filter valid readings
    valid_readings = [r for r in readings if r.value is not None and r.timestamp is not None]
    
    if len(valid_readings) < 2:
        return {
            "variability_metrics": {
                "standard_deviation": None,
                "coefficient_of_variation": None,
                "glucose_management_indicator": None
            },
            "explanations": {
                "standard_deviation": "Not enough data to calculate variability (need at least 2 readings)",
                "coefficient_of_variation": "Not enough data to calculate variability (need at least 2 readings)",
                "glucose_management_indicator": "Not enough data to calculate GMI (need at least 2 readings)"
            },
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "total_readings": len(valid_readings),
                "include_explanations": include_explanations
            }
        }

    # Extract glucose values
    values = [r.value for r in valid_readings]
    mean_value = sum(values) / len(values)
    
    # Calculate Standard Deviation (SD)
    variance = sum((x - mean_value) ** 2 for x in values) / len(values)
    standard_deviation = variance ** 0.5
    
    # Calculate Coefficient of Variation (CV) - SD as percentage of mean
    coefficient_of_variation = (standard_deviation / mean_value) * 100 if mean_value > 0 else 0
    
    # Calculate Glucose Management Indicator (GMI) - estimated A1C equivalent
    # Formula: GMI = 3.31 + 0.02392 × mean glucose (mg/dl)
    glucose_management_indicator = 3.31 + (0.02392 * mean_value)
    
    # Prepare response
    variability_metrics = {
        "standard_deviation": round(standard_deviation, 2),
        "coefficient_of_variation": round(coefficient_of_variation, 2),
        "glucose_management_indicator": round(glucose_management_indicator, 2),
        "mean_glucose": round(mean_value, 2),
        "min_glucose": min(values),
        "max_glucose": max(values),
        "total_readings": len(values)
    }
    
    # Add plain-language explanations if requested
    explanations = {}
    if include_explanations:
        # SD explanations
        if standard_deviation < 20:
            sd_explanation = "Excellent! Your blood sugar is very stable with low variability."
        elif standard_deviation < 30:
            sd_explanation = "Good! Your blood sugar shows moderate stability."
        elif standard_deviation < 40:
            sd_explanation = "Fair. Your blood sugar has some variability that could be improved."
        else:
            sd_explanation = "High variability detected. Consider discussing with your healthcare provider."
        
        # CV explanations
        if coefficient_of_variation < 20:
            cv_explanation = "Great stability! Your blood sugar changes very little compared to your average."
        elif coefficient_of_variation < 30:
            cv_explanation = "Good stability. Your blood sugar changes moderately compared to your average."
        elif coefficient_of_variation < 40:
            cv_explanation = "Moderate variability. Your blood sugar changes more than ideal."
        else:
            cv_explanation = "High variability. Your blood sugar changes significantly compared to your average."
        
        # GMI explanations
        if glucose_management_indicator < 6.5:
            gmi_explanation = f"Excellent control! Your estimated A1C equivalent is {glucose_management_indicator:.1f}% (target is <7.0%)."
        elif glucose_management_indicator < 7.0:
            gmi_explanation = f"Good control! Your estimated A1C equivalent is {glucose_management_indicator:.1f}% (target is <7.0%)."
        elif glucose_management_indicator < 8.0:
            gmi_explanation = f"Fair control. Your estimated A1C equivalent is {glucose_management_indicator:.1f}% (target is <7.0%)."
        else:
            gmi_explanation = f"Needs improvement. Your estimated A1C equivalent is {glucose_management_indicator:.1f}% (target is <7.0%)."
        
        explanations = {
            "standard_deviation": sd_explanation,
            "coefficient_of_variation": cv_explanation,
            "glucose_management_indicator": gmi_explanation,
            "overall_assessment": _get_overall_assessment(standard_deviation, coefficient_of_variation, glucose_management_indicator)
        }
    
    meta = {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "total_readings": len(valid_readings),
        "include_explanations": include_explanations
    }
    
    result = {
        "variability_metrics": variability_metrics,
        "meta": meta
    }
    
    if include_explanations:
        result["explanations"] = explanations
    
    return result

def _get_overall_assessment(sd: float, cv: float, gmi: float) -> str:
    """Generate overall assessment based on all metrics."""
    good_metrics = 0
    total_metrics = 3
    
    if sd < 30:
        good_metrics += 1
    if cv < 30:
        good_metrics += 1
    if gmi < 7.0:
        good_metrics += 1
    
    if good_metrics == 3:
        return "Excellent overall glucose control! Keep up the great work."
    elif good_metrics == 2:
        return "Good overall control with room for improvement in one area."
    elif good_metrics == 1:
        return "Fair control. Consider discussing with your healthcare provider."
    else:
        return "Blood sugar control needs attention. Please consult with your healthcare provider."

@router.get("/glucose-events")
def glucose_events(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    hypo_threshold: float = Query(70, description="Hypoglycemia threshold (mg/dl)"),
    hyper_threshold: float = Query(180, description="Hyperglycemia threshold (mg/dl)"),
    max_gap_minutes: int = Query(60, description="Maximum gap between readings to consider as same event (minutes)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns hypo- and hyperglycemia events with start/end times and durations for event timeline visualizations.
    An event starts when glucose crosses the threshold and ends when it returns to normal range.
    """
    # Determine date range based on window
    now = datetime.now(UTC)
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
        start = start_date
        end = end_date

    # Query glucose readings for the user in the date range
    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    readings = session.exec(query).all()
    
    # Filter valid readings and sort by timestamp
    valid_readings = [r for r in readings if r.value is not None and r.timestamp is not None]
    valid_readings.sort(key=lambda r: r.timestamp)
    
    if len(valid_readings) < 2:
        return {
            "events": [],
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "hypo_threshold": hypo_threshold,
                "hyper_threshold": hyper_threshold,
                "max_gap_minutes": max_gap_minutes,
                "total_readings": len(valid_readings)
            }
        }

    events = []
    current_event = None
    
    for i, reading in enumerate(valid_readings):
        value = reading.value
        timestamp = reading.timestamp
        
        # Determine if this reading is in hypo or hyper range
        if value < hypo_threshold:
            event_type = "hypo"
        elif value > hyper_threshold:
            event_type = "hyper"
        else:
            # Reading is in normal range - end current event if exists
            if current_event:
                current_event["end"] = valid_readings[i-1].timestamp.isoformat()
                current_event["duration_minutes"] = int((valid_readings[i-1].timestamp - current_event["start_dt"]).total_seconds() / 60)
                events.append(current_event)
                current_event = None
            continue
        
        # Check if we should start a new event
        if current_event is None:
            # Start new event
            current_event = {
                "type": event_type,
                "start": timestamp.isoformat(),
                "start_dt": timestamp,  # Keep datetime object for calculations
                "min_value": value,
                "max_value": value,
                "num_readings": 1
            }
        elif current_event["type"] == event_type:
            # Continue current event
            current_event["max_value"] = max(current_event["max_value"], value)
            current_event["min_value"] = min(current_event["min_value"], value)
            current_event["num_readings"] += 1
            
            # Check if gap is too large (start new event)
            if i > 0:
                time_diff = (timestamp - valid_readings[i-1].timestamp).total_seconds() / 60
                if time_diff > max_gap_minutes:
                    # End current event and start new one
                    current_event["end"] = valid_readings[i-1].timestamp.isoformat()
                    current_event["duration_minutes"] = int((valid_readings[i-1].timestamp - current_event["start_dt"]).total_seconds() / 60)
                    events.append(current_event)
                    
                    # Start new event
                    current_event = {
                        "type": event_type,
                        "start": timestamp.isoformat(),
                        "start_dt": timestamp,
                        "min_value": value,
                        "max_value": value,
                        "num_readings": 1
                    }
        else:
            # Different event type - end current event and start new one
            current_event["end"] = valid_readings[i-1].timestamp.isoformat()
            current_event["duration_minutes"] = int((valid_readings[i-1].timestamp - current_event["start_dt"]).total_seconds() / 60)
            events.append(current_event)
            
            # Start new event
            current_event = {
                "type": event_type,
                "start": timestamp.isoformat(),
                "start_dt": timestamp,
                "min_value": value,
                "max_value": value,
                "num_readings": 1
            }
    
    # Handle last event if it exists
    if current_event:
        current_event["end"] = valid_readings[-1].timestamp.isoformat()
        current_event["duration_minutes"] = int((valid_readings[-1].timestamp - current_event["start_dt"]).total_seconds() / 60)
        events.append(current_event)
    
    # Remove internal datetime object from events
    for event in events:
        del event["start_dt"]
    
    meta = {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "hypo_threshold": hypo_threshold,
        "hyper_threshold": hyper_threshold,
        "max_gap_minutes": max_gap_minutes,
        "total_readings": len(valid_readings),
        "total_events": len(events)
    }
    
    return {
        "events": events,
        "meta": meta
    }

@router.get("/meal-impact")
def meal_impact(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    group_by: str = Query("time_of_day", description="Group by 'meal_type' or 'time_of_day'"),
    pre_meal_minutes: int = Query(30, description="Minutes before meal to look for glucose reading"),
    post_meal_minutes: int = Query(120, description="Minutes after meal to look for glucose reading"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns average glucose change after meals, grouped by meal type or time of day.
    Analyzes glucose readings before and after meals to show impact on blood sugar.
    """
    # Determine date range based on window
    now = datetime.now(UTC)
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
        start = start_date
        end = end_date

    # Validate group_by parameter
    if group_by not in ["meal_type", "time_of_day"]:
        raise HTTPException(status_code=400, detail="group_by must be 'meal_type' or 'time_of_day'")

    # Query meals for the user in the date range
    meal_query = select(Meal).where(Meal.user_id == current_user.id)
    if start:
        meal_query = meal_query.where(Meal.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        meal_query = meal_query.where(Meal.timestamp <= datetime.combine(end, datetime.max.time()))
    meals = session.exec(meal_query).all()
    
    # Filter valid meals with timestamps
    valid_meals = [m for m in meals if m.timestamp is not None]
    
    if not valid_meals:
        return {
            "meal_impacts": [],
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "group_by": group_by,
                "pre_meal_minutes": pre_meal_minutes,
                "post_meal_minutes": post_meal_minutes,
                "total_meals_analyzed": 0
            }
        }

    # Query all glucose readings for the user in the date range
    glucose_query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        glucose_query = glucose_query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        glucose_query = glucose_query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    glucose_readings = session.exec(glucose_query).all()
    
    # Filter valid glucose readings and ensure timezone awareness
    valid_readings = []
    for r in glucose_readings:
        if r.value is not None and r.timestamp is not None:
            # Ensure reading timestamp is timezone-aware
            reading_time = r.timestamp
            if reading_time.tzinfo is None:
                # If naive datetime, assume it's in UTC
                reading_time = reading_time.replace(tzinfo=UTC)
            elif reading_time.tzinfo != UTC:
                # Convert to UTC if it's in a different timezone
                reading_time = reading_time.astimezone(UTC)
            
            # Store the timezone-aware timestamp for comparison
            r._timezone_aware_timestamp = reading_time
            valid_readings.append(r)
    
    valid_readings.sort(key=lambda r: r._timezone_aware_timestamp)
    
    if not valid_readings:
        return {
            "meal_impacts": [],
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "group_by": group_by,
                "pre_meal_minutes": pre_meal_minutes,
                "post_meal_minutes": post_meal_minutes,
                "total_meals_analyzed": 0
            }
        }

    # Analyze each meal
    meal_impacts = []
    total_meals_analyzed = 0
    
    for meal in valid_meals:
        meal_time = meal.timestamp
        # Ensure meal_time is timezone-aware and convert to UTC if needed
        if meal_time and meal_time.tzinfo is None:
            # If naive datetime, assume it's in UTC
            meal_time = meal_time.replace(tzinfo=UTC)
        elif meal_time and meal_time.tzinfo != UTC:
            # Convert to UTC if it's in a different timezone
            meal_time = meal_time.astimezone(UTC)
        
        # Find pre-meal glucose reading (closest reading within pre_meal_minutes before meal)
        pre_meal_reading = None
        for reading in valid_readings:
            if reading._timezone_aware_timestamp <= meal_time and (meal_time - reading._timezone_aware_timestamp).total_seconds() / 60 <= pre_meal_minutes:
                if pre_meal_reading is None or reading._timezone_aware_timestamp > pre_meal_reading._timezone_aware_timestamp:
                    pre_meal_reading = reading
        
        # Find post-meal glucose reading (closest reading within post_meal_minutes after meal)
        post_meal_reading = None
        for reading in valid_readings:
            if reading._timezone_aware_timestamp >= meal_time and (reading._timezone_aware_timestamp - meal_time).total_seconds() / 60 <= post_meal_minutes:
                if post_meal_reading is None or reading._timezone_aware_timestamp < post_meal_reading._timezone_aware_timestamp:
                    post_meal_reading = reading
        
        # Only analyze if we have both pre and post readings
        if pre_meal_reading and post_meal_reading:
            glucose_change = post_meal_reading.value - pre_meal_reading.value
            
            # Determine group based on group_by parameter
            if group_by == "meal_type":
                # Since Meal model doesn't have meal_type field, we'll derive it from description or time
                if meal.description:
                    desc_lower = meal.description.lower()
                    if any(word in desc_lower for word in ["breakfast", "morning", "cereal", "toast", "eggs"]):
                        group = "breakfast"
                    elif any(word in desc_lower for word in ["lunch", "noon", "sandwich", "salad"]):
                        group = "lunch"
                    elif any(word in desc_lower for word in ["dinner", "evening", "supper", "pasta", "meat"]):
                        group = "dinner"
                    elif any(word in desc_lower for word in ["snack", "coffee", "tea", "fruit"]):
                        group = "snack"
                    else:
                        # Fall back to time-based grouping
                        hour = meal_time.hour
                        if 5 <= hour < 11:
                            group = "breakfast"
                        elif 11 <= hour < 16:
                            group = "lunch"
                        elif 16 <= hour < 21:
                            group = "dinner"
                        else:
                            group = "snack"
                else:
                    # No description, use time-based grouping
                    hour = meal_time.hour
                    if 5 <= hour < 11:
                        group = "breakfast"
                    elif 11 <= hour < 16:
                        group = "lunch"
                    elif 16 <= hour < 21:
                        group = "dinner"
                    else:
                        group = "snack"
            else:  # time_of_day
                hour = meal_time.hour
                if 5 <= hour < 11:
                    group = "breakfast"
                elif 11 <= hour < 16:
                    group = "lunch"
                elif 16 <= hour < 21:
                    group = "dinner"
                else:
                    group = "snack"
            
            meal_impacts.append({
                "group": group,
                "glucose_change": glucose_change,
                "pre_meal_glucose": pre_meal_reading.value,
                "post_meal_glucose": post_meal_reading.value,
                "meal_timestamp": meal_time.isoformat(),
                "pre_meal_timestamp": pre_meal_reading._timezone_aware_timestamp.isoformat(),
                "post_meal_timestamp": post_meal_reading._timezone_aware_timestamp.isoformat()
            })
            total_meals_analyzed += 1
    
    # Group and calculate statistics
    grouped_impacts = {}
    for impact in meal_impacts:
        group = impact["group"]
        if group not in grouped_impacts:
            grouped_impacts[group] = []
        grouped_impacts[group].append(impact)
    
    # Calculate averages for each group
    result_impacts = []
    for group, impacts in grouped_impacts.items():
        glucose_changes = [impact["glucose_change"] for impact in impacts]
        pre_meal_values = [impact["pre_meal_glucose"] for impact in impacts]
        post_meal_values = [impact["post_meal_glucose"] for impact in impacts]
        
        avg_glucose_change = sum(glucose_changes) / len(glucose_changes)
        avg_pre_meal = sum(pre_meal_values) / len(pre_meal_values)
        avg_post_meal = sum(post_meal_values) / len(post_meal_values)
        
        # Calculate standard deviation
        if len(glucose_changes) > 1:
            mean_change = sum(glucose_changes) / len(glucose_changes)
            variance = sum((x - mean_change) ** 2 for x in glucose_changes) / len(glucose_changes)
            std_dev_change = variance ** 0.5
        else:
            std_dev_change = 0.0
        
        result_impacts.append({
            "group": group,
            "avg_glucose_change": round(avg_glucose_change, 2),
            "num_meals": len(impacts),
            "avg_pre_meal": round(avg_pre_meal, 2),
            "avg_post_meal": round(avg_post_meal, 2),
            "std_dev_change": round(std_dev_change, 2)
        })
    
    # Sort by group name for consistent output
    result_impacts.sort(key=lambda x: x["group"])
    
    meta = {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "group_by": group_by,
        "pre_meal_minutes": pre_meal_minutes,
        "post_meal_minutes": post_meal_minutes,
        "total_meals_analyzed": total_meals_analyzed
    }
    
    return {
        "meal_impacts": result_impacts,
        "meta": meta
    }
