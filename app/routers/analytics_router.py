from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.activity import Activity
from app.models.insulin_dose import InsulinDose
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
    start_datetime: Optional[datetime] = Query(None, description="Start datetime (ISO 8601, UTC preferred)"),
    end_datetime: Optional[datetime] = Query(None, description="End datetime (ISO 8601, UTC preferred)"),
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
    # Determine date/time range based on window or explicit datetimes
    now = datetime.now(UTC)
    if start_datetime or end_datetime:
        # Frontend always sends UTC datetimes, so we can use them directly
        start = start_datetime
        end = end_datetime
    elif window == "day":
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

    # Query meals for the user in the date/time range
    meal_query = select(Meal).where(Meal.user_id == current_user.id)
    if isinstance(start, datetime):
        meal_query = meal_query.where(Meal.timestamp >= start)
    elif start:
        meal_query = meal_query.where(Meal.timestamp >= datetime.combine(start, datetime.min.time()))
    if isinstance(end, datetime):
        meal_query = meal_query.where(Meal.timestamp <= end)
    elif end:
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
    if isinstance(start, datetime):
        glucose_query = glucose_query.where(GlucoseReading.timestamp >= start)
    elif start:
        glucose_query = glucose_query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if isinstance(end, datetime):
        glucose_query = glucose_query.where(GlucoseReading.timestamp <= end)
    elif end:
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


@router.get("/activity-impact")
def activity_impact(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    group_by: str = Query("activity_type", description="Group by 'activity_type' or 'intensity'"),
    pre_activity_minutes: int = Query(30, description="Minutes before activity to look for glucose reading"),
    post_activity_minutes: int = Query(120, description="Minutes after activity to look for glucose reading"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns average glucose change after activities, grouped by activity type or intensity.
    Analyzes glucose readings before and after activities to show impact on blood sugar.
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
    if group_by not in ["activity_type", "intensity"]:
        raise HTTPException(status_code=400, detail="group_by must be 'activity_type' or 'intensity'")

    # Query activities for the user in the date range
    activity_query = select(Activity).where(Activity.user_id == current_user.id)
    if start:
        activity_query = activity_query.where(Activity.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        activity_query = activity_query.where(Activity.timestamp <= datetime.combine(end, datetime.max.time()))
    activities = session.exec(activity_query).all()

    # Filter valid activities with timestamps
    valid_activities = [a for a in activities if a.timestamp is not None]

    if not valid_activities:
        return {
            "activity_impacts": [],
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "group_by": group_by,
                "pre_activity_minutes": pre_activity_minutes,
                "post_activity_minutes": post_activity_minutes,
                "total_activities_analyzed": 0
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
    for reading in glucose_readings:
        if reading.value is not None and reading.timestamp is not None:
            # Ensure reading timestamp is timezone-aware
            reading_time = reading.timestamp
            if reading_time.tzinfo is None:
                # If naive datetime, assume it's in UTC
                reading_time = reading_time.replace(tzinfo=UTC)
            elif reading_time.tzinfo != UTC:
                # Convert to UTC if it's in a different timezone
                reading_time = reading_time.astimezone(UTC)

            # Store the timezone-aware timestamp for comparison
            reading._timezone_aware_timestamp = reading_time
            valid_readings.append(reading)

    valid_readings.sort(key=lambda r: r._timezone_aware_timestamp)

    if not valid_readings:
        return {
            "activity_impacts": [],
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "group_by": group_by,
                "pre_activity_minutes": pre_activity_minutes,
                "post_activity_minutes": post_activity_minutes,
                "total_activities_analyzed": 0
            }
        }

    # Analyze each activity
    activity_impacts = []
    total_activities_analyzed = 0

    for activity in valid_activities:
        # Use start_time if available, otherwise fall back to timestamp
        activity_time = activity.start_time or activity.timestamp
        # Ensure activity_time is timezone-aware and convert to UTC if needed
        if activity_time and activity_time.tzinfo is None:
            # If naive datetime, assume it's in UTC
            activity_time = activity_time.replace(tzinfo=UTC)
        elif activity_time and activity_time.tzinfo != UTC:
            # Convert to UTC if it's in a different timezone
            activity_time = activity_time.astimezone(UTC)

        # Find pre-activity glucose reading (closest reading within pre_activity_minutes before activity)
        pre_activity_reading = None
        for reading in valid_readings:
            if reading._timezone_aware_timestamp <= activity_time and (activity_time - reading._timezone_aware_timestamp).total_seconds() / 60 <= pre_activity_minutes:
                if pre_activity_reading is None or reading._timezone_aware_timestamp > pre_activity_reading._timezone_aware_timestamp:
                    pre_activity_reading = reading

        # Find post-activity glucose reading (closest reading within post_activity_minutes after activity)
        post_activity_reading = None
        for reading in valid_readings:
            if reading._timezone_aware_timestamp >= activity_time and (reading._timezone_aware_timestamp - activity_time).total_seconds() / 60 <= post_activity_minutes:
                if post_activity_reading is None or reading._timezone_aware_timestamp < post_activity_reading._timezone_aware_timestamp:
                    post_activity_reading = reading

        if pre_activity_reading and post_activity_reading:
            glucose_change = post_activity_reading.value - pre_activity_reading.value

            # Determine group based on group_by parameter
            if group_by == "activity_type":
                # Use activity type from the activity record
                group = activity.type.lower() if activity.type else "unknown"
            else:  # intensity
                # Group by intensity level
                if activity.intensity:
                    intensity_lower = activity.intensity.lower()
                    if any(word in intensity_lower for word in ["low", "light", "easy"]):
                        group = "low"
                    elif any(word in intensity_lower for word in ["medium", "moderate", "mod"]):
                        group = "medium"
                    elif any(word in intensity_lower for word in ["high", "intense", "vigorous"]):
                        group = "high"
                    else:
                        group = "unknown"
                else:
                    group = "unknown"

            activity_impacts.append({
                "group": group,
                "glucose_change": glucose_change,
                "pre_activity_glucose": pre_activity_reading.value,
                "post_activity_glucose": post_activity_reading.value,
                "activity_timestamp": activity_time.isoformat(),
                "pre_activity_timestamp": pre_activity_reading._timezone_aware_timestamp.isoformat(),
                "post_activity_timestamp": post_activity_reading._timezone_aware_timestamp.isoformat(),
                "activity_duration": activity.duration_min,
                "calories_burned": activity.calories_burned
            })
            total_activities_analyzed += 1

    # Group and calculate statistics
    grouped_impacts = {}
    for impact in activity_impacts:
        group = impact["group"]
        if group not in grouped_impacts:
            grouped_impacts[group] = []
        grouped_impacts[group].append(impact)

    # Calculate averages for each group
    result_impacts = []
    for group, impacts in grouped_impacts.items():
        glucose_changes = [impact["glucose_change"] for impact in impacts]
        pre_activity_values = [impact["pre_activity_glucose"] for impact in impacts]
        post_activity_values = [impact["post_activity_glucose"] for impact in impacts]

        avg_glucose_change = sum(glucose_changes) / len(glucose_changes)
        avg_pre_activity = sum(pre_activity_values) / len(pre_activity_values)
        avg_post_activity = sum(post_activity_values) / len(post_activity_values)

        # Calculate standard deviation
        if len(glucose_changes) > 1:
            mean_change = sum(glucose_changes) / len(glucose_changes)
            variance = sum((x - mean_change) ** 2 for x in glucose_changes) / len(glucose_changes)
            std_dev_change = variance ** 0.5
        else:
            std_dev_change = 0.0

        # Calculate average duration and calories for this group
        avg_duration = sum(impact["activity_duration"] for impact in impacts if impact["activity_duration"]) / len([impact for impact in impacts if impact["activity_duration"]]) if any(impact["activity_duration"] for impact in impacts) else None
        avg_calories = sum(impact["calories_burned"] for impact in impacts if impact["calories_burned"]) / len([impact for impact in impacts if impact["calories_burned"]]) if any(impact["calories_burned"] for impact in impacts) else None

        result_impacts.append({
            "group": group,
            "avg_glucose_change": round(avg_glucose_change, 2),
            "num_activities": len(impacts),
            "avg_pre_activity": round(avg_pre_activity, 2),
            "avg_post_activity": round(avg_post_activity, 2),
            "std_dev_change": round(std_dev_change, 2),
            "avg_duration_minutes": round(avg_duration, 1) if avg_duration else None,
            "avg_calories_burned": round(avg_calories, 1) if avg_calories else None
        })

    # Sort by group name for consistent output
    result_impacts.sort(key=lambda x: x["group"])

    meta = {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "group_by": group_by,
        "pre_activity_minutes": pre_activity_minutes,
        "post_activity_minutes": post_activity_minutes,
        "total_activities_analyzed": total_activities_analyzed
    }

    return {
        "activity_impacts": result_impacts,
        "meta": meta
    }


@router.get("/insulin-glucose-correlation")
def insulin_glucose_correlation(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    start_datetime: Optional[datetime] = Query(None, description="Start datetime (ISO 8601, UTC preferred)"),
    end_datetime: Optional[datetime] = Query(None, description="End datetime (ISO 8601, UTC preferred)"),
    group_by: str = Query("dose_range", description="Group by 'dose_range', 'time_of_day', or 'insulin_effectiveness'"),
    pre_insulin_minutes: int = Query(30, description="Minutes before insulin to look for glucose reading"),
    post_insulin_minutes: int = Query(180, description="Minutes after insulin to look for glucose reading"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns correlation analysis between insulin doses and glucose changes.
    Analyzes how insulin doses affect glucose levels for personalized insights.
    """
    # Determine date/time range based on window or explicit datetimes
    now = datetime.now(UTC)
    if start_datetime or end_datetime:
        # Frontend always sends UTC datetimes, so we can use them directly
        start = start_datetime
        end = end_datetime
    elif window == "day":
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
    if group_by not in ["dose_range", "time_of_day", "insulin_effectiveness"]:
        raise HTTPException(status_code=400, detail="group_by must be 'dose_range', 'time_of_day', or 'insulin_effectiveness'")

    # Query insulin doses for the user in the date range
    insulin_query = select(InsulinDose).where(InsulinDose.user_id == current_user.id)
    if isinstance(start, datetime):
        insulin_query = insulin_query.where(InsulinDose.timestamp >= start)
    elif start:
        insulin_query = insulin_query.where(InsulinDose.timestamp >= datetime.combine(start, datetime.min.time()))
    if isinstance(end, datetime):
        insulin_query = insulin_query.where(InsulinDose.timestamp <= end)
    elif end:
        insulin_query = insulin_query.where(InsulinDose.timestamp <= datetime.combine(end, datetime.max.time()))
    insulin_doses = session.exec(insulin_query).all()

    # Filter valid insulin doses with timestamps
    valid_doses = [d for d in insulin_doses if d.timestamp is not None and d.units > 0]

    if not valid_doses:
        return {
            "correlations": [],
            "overall_analysis": {
                "total_doses_analyzed": 0,
                "avg_insulin_sensitivity": None,
                "most_effective_dose_range": None,
                "recommendations": [f"No insulin doses found in the specified time range. Found {len(insulin_doses)} total doses, {len([d for d in insulin_doses if d.timestamp is not None])} with timestamps, {len([d for d in insulin_doses if d.units > 0])} with valid units"]
            },
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "group_by": group_by,
                "pre_insulin_minutes": pre_insulin_minutes,
                "post_insulin_minutes": post_insulin_minutes
            }
        }

    # Query all glucose readings for the user in the date range
    glucose_query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if isinstance(start, datetime):
        glucose_query = glucose_query.where(GlucoseReading.timestamp >= start)
    elif start:
        glucose_query = glucose_query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if isinstance(end, datetime):
        glucose_query = glucose_query.where(GlucoseReading.timestamp <= end)
    elif end:
        glucose_query = glucose_query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    glucose_readings = session.exec(glucose_query).all()

    # Filter valid glucose readings
    valid_readings = []
    for reading in glucose_readings:
        if reading.value is not None and reading.timestamp is not None:
            # Database timestamps are already timezone-aware UTC
            reading_time = reading.timestamp
            # Store the timestamp for comparison
            reading._timezone_aware_timestamp = reading_time
            valid_readings.append(reading)

    valid_readings.sort(key=lambda r: r._timezone_aware_timestamp)

    if not valid_readings:
        return {
            "correlations": [],
            "overall_analysis": {
                "total_doses_analyzed": 0,
                "avg_insulin_sensitivity": None,
                "most_effective_dose_range": None,
                "recommendations": ["No glucose readings found in the specified time range"]
            },
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "group_by": group_by,
                "pre_insulin_minutes": pre_insulin_minutes,
                "post_insulin_minutes": post_insulin_minutes
            }
        }

    # Analyze each insulin dose
    dose_glucose_pairs = []
    total_doses_analyzed = 0

    for dose in valid_doses:
        dose_time = dose.timestamp
        # Database timestamps are already timezone-aware UTC

        # Find pre-insulin glucose reading (closest reading within pre_insulin_minutes before dose)
        pre_insulin_reading = None
        for reading in valid_readings:
            if reading._timezone_aware_timestamp <= dose_time and (dose_time - reading._timezone_aware_timestamp).total_seconds() / 60 <= pre_insulin_minutes:
                if pre_insulin_reading is None or reading._timezone_aware_timestamp > pre_insulin_reading._timezone_aware_timestamp:
                    pre_insulin_reading = reading

        # Find post-insulin glucose reading (closest reading within post_insulin_minutes after dose)
        post_insulin_reading = None
        for reading in valid_readings:
            if reading._timezone_aware_timestamp >= dose_time and (reading._timezone_aware_timestamp - dose_time).total_seconds() / 60 <= post_insulin_minutes:
                if post_insulin_reading is None or reading._timezone_aware_timestamp < post_insulin_reading._timezone_aware_timestamp:
                    post_insulin_reading = reading

        if pre_insulin_reading and post_insulin_reading:
            glucose_change = post_insulin_reading.value - pre_insulin_reading.value
            insulin_sensitivity = glucose_change / dose.units if dose.units > 0 else 0

            # Calculate response time (minutes from dose to post-insulin reading)
            response_time = (post_insulin_reading._timezone_aware_timestamp - dose_time).total_seconds() / 60

            # Determine group based on group_by parameter
            if group_by == "dose_range":
                if dose.units <= 2:
                    group = "0-2_units"
                elif dose.units <= 5:
                    group = "2-5_units"
                else:
                    group = "5+_units"
            elif group_by == "time_of_day":
                hour = dose_time.hour
                if 6 <= hour < 12:
                    group = "morning"
                elif 12 <= hour < 18:
                    group = "afternoon"
                elif 18 <= hour < 24:
                    group = "evening"
                else:
                    group = "night"
            else:  # insulin_effectiveness
                if insulin_sensitivity <= -30:
                    group = "high_sensitivity"
                elif insulin_sensitivity <= -15:
                    group = "medium_sensitivity"
                else:
                    group = "low_sensitivity"

            dose_glucose_pairs.append({
                "group": group,
                "insulin_units": dose.units,
                "glucose_change": glucose_change,
                "insulin_sensitivity": insulin_sensitivity,
                "pre_insulin_glucose": pre_insulin_reading.value,
                "post_insulin_glucose": post_insulin_reading.value,
                "response_time_minutes": response_time,
                "dose_timestamp": dose_time.isoformat(),
                "pre_glucose_timestamp": pre_insulin_reading._timezone_aware_timestamp.isoformat(),
                "post_glucose_timestamp": post_insulin_reading._timezone_aware_timestamp.isoformat()
            })
            total_doses_analyzed += 1

    if not dose_glucose_pairs:
        return {
            "correlations": [],
            "overall_analysis": {
                "total_doses_analyzed": 0,
                "avg_insulin_sensitivity": None,
                "most_effective_dose_range": None,
                "recommendations": ["No valid insulin-glucose pairs found"]
            },
            "meta": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "group_by": group_by,
                "pre_insulin_minutes": pre_insulin_minutes,
                "post_insulin_minutes": post_insulin_minutes
            }
        }

    # Group and calculate statistics
    grouped_pairs = {}
    for pair in dose_glucose_pairs:
        group = pair["group"]
        if group not in grouped_pairs:
            grouped_pairs[group] = []
        grouped_pairs[group].append(pair)

    # Calculate correlations for each group
    correlations = []
    all_sensitivities = []

    for group, pairs in grouped_pairs.items():
        # Allow single pairs for basic analysis, but note limited correlation
        if len(pairs) < 1:
            continue

        insulin_units = [pair["insulin_units"] for pair in pairs]
        glucose_changes = [pair["glucose_change"] for pair in pairs]
        sensitivities = [pair["insulin_sensitivity"] for pair in pairs]
        response_times = [pair["response_time_minutes"] for pair in pairs]

        # Calculate averages
        avg_glucose_change = sum(glucose_changes) / len(glucose_changes)
        avg_insulin_units = sum(insulin_units) / len(insulin_units)
        avg_sensitivity = sum(sensitivities) / len(sensitivities)
        avg_response_time = sum(response_times) / len(response_times)

        # Calculate correlation coefficient (simplified Pearson correlation)
        if len(pairs) > 1:
            # Calculate correlation between insulin units and glucose change
            mean_units = sum(insulin_units) / len(insulin_units)
            mean_change = sum(glucose_changes) / len(glucose_changes)

            numerator = sum((u - mean_units) * (g - mean_change) for u, g in zip(insulin_units, glucose_changes))
            denominator_units = sum((u - mean_units) ** 2 for u in insulin_units)
            denominator_change = sum((g - mean_change) ** 2 for g in glucose_changes)

            if denominator_units > 0 and denominator_change > 0:
                correlation_coefficient = numerator / (denominator_units * denominator_change) ** 0.5
            else:
                correlation_coefficient = 0.0
        else:
            # For single pairs, correlation is not meaningful
            correlation_coefficient = None

        # Calculate standard deviation
        if len(glucose_changes) > 1:
            mean_change = sum(glucose_changes) / len(glucose_changes)
            variance = sum((x - mean_change) ** 2 for x in glucose_changes) / len(glucose_changes)
            std_dev_change = variance ** 0.5
        else:
            std_dev_change = 0.0

        # Calculate effectiveness score (0-1, higher is better)
        # Based on glucose drop, consistency, and response time
        glucose_drop_score = min(abs(avg_glucose_change) / 50.0, 1.0)  # Normalize to 50 mg/dl drop
        consistency_score = max(1.0 - (std_dev_change / 30.0), 0.0) if std_dev_change is not None else 0.5  # Lower std dev is better
        response_time_score = max(1.0 - (avg_response_time - 45) / 60.0, 0.0)  # 45 min is optimal

        effectiveness_score = (glucose_drop_score * 0.4 + consistency_score * 0.3 + response_time_score * 0.3)
        effectiveness_score = max(0.0, min(1.0, effectiveness_score))  # Clamp to 0-1

        correlations.append({
            "group": group,
            "avg_glucose_change": round(avg_glucose_change, 2),
            "avg_insulin_units": round(avg_insulin_units, 2),
            "insulin_sensitivity": round(avg_sensitivity, 2),
            "num_doses": len(pairs),
            "response_time_minutes": round(avg_response_time, 1),
            "effectiveness_score": round(effectiveness_score, 3),
            "correlation_coefficient": correlation_coefficient,
            "std_dev_change": std_dev_change
        })

        all_sensitivities.extend(sensitivities)

    # Sort by group name for consistent output
    correlations.sort(key=lambda x: x["group"])

    # Calculate overall analysis
    overall_avg_sensitivity = sum(all_sensitivities) / len(all_sensitivities) if all_sensitivities else None

    # Find most effective dose range
    most_effective_group = None
    if correlations:
        most_effective_group = max(correlations, key=lambda x: x["effectiveness_score"])["group"]

    # Generate recommendations
    recommendations = []
    if total_doses_analyzed < 10:
        recommendations.append("Need more data - analyze at least 10 insulin doses for reliable insights")
    else:
        if overall_avg_sensitivity and overall_avg_sensitivity < -30:
            recommendations.append("High insulin sensitivity - be careful with dose increases")
        elif overall_avg_sensitivity and overall_avg_sensitivity > -10:
            recommendations.append("Low insulin sensitivity - may need higher doses or consult healthcare provider")

        if correlations:
            best_group = max(correlations, key=lambda x: x["effectiveness_score"])
            recommendations.append(f"Most effective: {best_group} (effectiveness: {best_group['effectiveness_score']:.1%})")

    overall_analysis = {
        "total_doses_analyzed": total_doses_analyzed,
        "avg_insulin_sensitivity": round(overall_avg_sensitivity, 2) if overall_avg_sensitivity else None,
        "most_effective_dose_range": most_effective_group,
        "recommendations": recommendations
    }

    meta = {
        "start_date": start.isoformat() if start else None,
        "end_date": end.isoformat() if end else None,
        "group_by": group_by,
        "pre_insulin_minutes": pre_insulin_minutes,
        "post_insulin_minutes": post_insulin_minutes
    }

    return {
        "correlations": correlations,
        "overall_analysis": overall_analysis,
        "meta": meta
    }


@router.get("/recommendations")
def recommendations(
    window: Optional[str] = Query(None, description="Predefined window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    include_alerts: bool = Query(True, description="Include urgent alerts and warnings"),
    include_tips: bool = Query(True, description="Include actionable tips and suggestions"),
    include_trends: bool = Query(True, description="Include trend analysis and insights"),
    include_ai_insights: bool = Query(True, description="Include AI-generated personalized insights"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns personalized recommendations based on recent data analysis.
    Provides actionable tips, alerts, and insights for diabetes management.
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

    # Query recent data for analysis
    glucose_query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        glucose_query = glucose_query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        glucose_query = glucose_query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    glucose_readings = session.exec(glucose_query).all()
    glucose_readings = [r for r in glucose_readings if r.value is not None and r.timestamp is not None]

    meal_query = select(Meal).where(Meal.user_id == current_user.id)
    if start:
        meal_query = meal_query.where(Meal.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        meal_query = meal_query.where(Meal.timestamp <= datetime.combine(end, datetime.max.time()))
    meals = session.exec(meal_query).all()

    activity_query = select(Activity).where(Activity.user_id == current_user.id)
    if start:
        activity_query = activity_query.where(Activity.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        activity_query = activity_query.where(Activity.timestamp <= datetime.combine(end, datetime.max.time()))
    activities = session.exec(activity_query).all()

    insulin_query = select(InsulinDose).where(InsulinDose.user_id == current_user.id)
    if start:
        insulin_query = insulin_query.where(InsulinDose.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        insulin_query = insulin_query.where(InsulinDose.timestamp <= datetime.combine(end, datetime.max.time()))
    insulin_doses = session.exec(insulin_query).all()

    recommendations = {
        "alerts": [],
        "tips": [],
        "trends": [],
        "ai_insights": [],
        "summary": {
            "total_glucose_readings": len(glucose_readings),
            "total_meals": len(meals),
            "total_activities": len(activities),
            "total_insulin_doses": len(insulin_doses),
            "analysis_period": {
                "start_date": start.isoformat() if start else None,
                "end_date": end.isoformat() if end else None,
                "days_analyzed": (end - start).days + 1 if start and end else None
            }
        }
    }

    if not glucose_readings:
        recommendations["alerts"].append({
            "type": "info",
            "priority": "medium",
            "message": "No glucose readings found in the specified period. Consider adding more data for personalized recommendations.",
            "action": "Add glucose readings to get personalized insights"
        })
        return recommendations

    # Calculate basic metrics
    glucose_values = [r.value for r in glucose_readings]
    avg_glucose = sum(glucose_values) / len(glucose_values)
    min_glucose = min(glucose_values)
    max_glucose = max(glucose_values)

    # Calculate time in target range (70-180 mg/dl)
    in_target = [v for v in glucose_values if 70 <= v <= 180]
    time_in_target = (len(in_target) / len(glucose_values)) * 100

    # Calculate coefficient of variation (CV)
    if len(glucose_values) > 1:
        mean = sum(glucose_values) / len(glucose_values)
        variance = sum((x - mean) ** 2 for x in glucose_values) / (len(glucose_values) - 1)
        std_dev = math.sqrt(variance)
        cv = (std_dev / mean) * 100
    else:
        cv = 0.0

    # Generate alerts
    if include_alerts:
        # High glucose alerts
        if avg_glucose > 200:
            recommendations["alerts"].append({
                "type": "warning",
                "priority": "high",
                "message": f"Average glucose is high ({avg_glucose:.0f} mg/dl). Consider adjusting insulin or meal timing.",
                "action": "Review recent meals and insulin doses"
            })

        if max_glucose > 300:
            recommendations["alerts"].append({
                "type": "warning",
                "priority": "high",
                "message": f"Maximum glucose reading is very high ({max_glucose:.0f} mg/dl).",
                "action": "Check for ketones and contact healthcare provider if needed"
            })

        if min_glucose < 70:
            recommendations["alerts"].append({
                "type": "warning",
                "priority": "medium",
                "message": f"Minimum glucose reading is low ({min_glucose:.0f} mg/dl).",
                "action": "Be prepared for hypoglycemia and carry fast-acting carbs"
            })

        if min_glucose < 54:
            recommendations["alerts"].append({
                "type": "warning",
                "priority": "high",
                "message": f"Severe hypoglycemia detected ({min_glucose:.0f} mg/dl).",
                "action": "Treat immediately and review insulin dosing"
            })

        if cv > 36:
            recommendations["alerts"].append({
                "type": "warning",
                "priority": "medium",
                "message": f"High glucose variability (CV: {cv:.1f}%).",
                "action": "Focus on consistent meal timing and insulin dosing"
            })

        if time_in_target < 70:
            recommendations["alerts"].append({
                "type": "warning",
                "priority": "medium",
                "message": f"Low time in target range ({time_in_target:.1f}%). Aim for at least 70%.",
                "action": "Review glucose management strategies"
            })

    # Generate tips
    if include_tips:
        # Meal tips
        if meals:
            avg_carbs = sum(m.total_carbs or 0 for m in meals) / len(meals)
            if avg_carbs > 60:
                recommendations["tips"].append({
                    "category": "nutrition",
                    "message": f"Average meal carbs are high ({avg_carbs:.0f}g). Consider smaller portions for better control.",
                    "priority": "medium"
                })
            elif avg_carbs < 30:
                recommendations["tips"].append({
                    "category": "nutrition",
                    "message": f"Average meal carbs are low ({avg_carbs:.0f}g). Ensure adequate nutrition.",
                    "priority": "medium"
                })
            else:
                recommendations["tips"].append({
                    "category": "nutrition",
                    "message": f"Average meal carbs are moderate ({avg_carbs:.0f}g). Consider smaller portions for better control.",
                    "priority": "medium"
                })

        # Activity tips
        if activities:
            avg_duration = sum(a.duration_min or 0 for a in activities) / len(activities)
            if avg_duration < 30:
                recommendations["tips"].append({
                    "category": "exercise",
                    "message": "Consider increasing activity duration for better glucose control.",
                    "priority": "medium"
                })

        # Insulin tips
        if insulin_doses:
            avg_insulin = sum(d.units for d in insulin_doses) / len(insulin_doses)
            if avg_insulin > 10:
                recommendations["tips"].append({
                    "category": "medication",
                    "message": f"High average insulin dose ({avg_insulin:.1f} units). Consider reviewing with healthcare provider.",
                    "priority": "medium"
                })

        # General management tips
        if len(glucose_readings) < 4:
            recommendations["tips"].append({
                "category": "monitoring",
                "message": "Limited glucose readings. More frequent monitoring provides better insights.",
                "priority": "medium"
            })

        if time_in_target < 80:
            recommendations["tips"].append({
                "category": "management",
                "message": "Focus on improving time in target range. Consider meal timing and insulin adjustments.",
                "priority": "high"
            })

    # Generate trends
    if include_trends and len(glucose_readings) > 1:
        # Sort readings by timestamp
        sorted_readings = sorted(glucose_readings, key=lambda x: x.timestamp)

        # Analyze recent vs earlier readings
        mid_point = len(sorted_readings) // 2
        earlier_readings = sorted_readings[:mid_point]
        recent_readings = sorted_readings[mid_point:]

        if earlier_readings and recent_readings:
            earlier_avg = sum(r.value for r in earlier_readings) / len(earlier_readings)
            recent_avg = sum(r.value for r in recent_readings) / len(recent_readings)

            if recent_avg > earlier_avg + 20:
                recommendations["trends"].append({
                    "type": "increasing",
                    "message": "Glucose levels are trending upward. Review recent changes in routine.",
                    "magnitude": "moderate" if recent_avg - earlier_avg < 50 else "significant"
                })
            elif recent_avg < earlier_avg - 20:
                recommendations["trends"].append({
                    "type": "decreasing",
                    "message": "Glucose levels are trending downward. Monitor for hypoglycemia.",
                    "magnitude": "moderate" if earlier_avg - recent_avg < 50 else "significant"
                })
            else:
                recommendations["trends"].append({
                    "type": "stable",
                    "message": "Glucose levels are relatively stable. Continue current management approach.",
                    "magnitude": "stable"
                })

        # Pattern analysis
        if cv < 20:
            recommendations["trends"].append({
                "type": "pattern",
                "message": "Excellent glucose stability detected. Your management is working well.",
                "magnitude": "positive"
            })
        elif cv > 40:
            recommendations["trends"].append({
                "type": "pattern",
                "message": "High glucose variability suggests inconsistent management. Focus on routine.",
                "magnitude": "concerning"
            })

    # Generate AI insights if requested
    if include_ai_insights:
        ai_insights = _generate_ai_insights(glucose_readings, meals, activities, insulin_doses, current_user)
        recommendations["ai_insights"] = ai_insights

    # Add summary insights
    if time_in_target > 80:
        recommendations["summary"]["overall_status"] = "excellent"
        recommendations["summary"]["status_message"] = "Great glucose control! Keep up the good work."
    elif time_in_target > 70:
        recommendations["summary"]["overall_status"] = "good"
        recommendations["summary"]["status_message"] = "Good glucose control with room for improvement."
    elif time_in_target > 50:
        recommendations["summary"]["overall_status"] = "fair"
        recommendations["summary"]["status_message"] = "Fair glucose control. Consider reviewing management strategies."
    else:
        recommendations["summary"]["overall_status"] = "needs_improvement"
        recommendations["summary"]["status_message"] = "Glucose control needs improvement. Consider consulting healthcare provider."

    recommendations["summary"]["key_metrics"] = {
        "average_glucose": round(avg_glucose, 1),
        "time_in_target": round(time_in_target, 1),
        "glucose_variability_cv": round(cv, 1),
        "glucose_range": f"{min_glucose:.0f} - {max_glucose:.0f}"
    }

    return recommendations


def _generate_ai_insights(
    glucose_readings: List[GlucoseReading],
    meals: List[Meal],
    activities: List[Activity],
    insulin_doses: List[InsulinDose],
    current_user: User
) -> List[Dict[str, Any]]:
    """
    Generate AI-powered personalized insights based on user's data patterns.
    Uses statistical analysis and pattern recognition to provide intelligent recommendations.
    """
    insights = []

    if not glucose_readings:
        return insights

    # Analyze glucose patterns for AI insights
    glucose_values = [r.value for r in glucose_readings]
    glucose_timestamps = [r.timestamp for r in glucose_readings]

    # 1. Pattern Recognition: Identify daily glucose patterns
    daily_patterns = _analyze_daily_patterns(glucose_readings)
    if daily_patterns:
        insights.append({
            "type": "pattern_recognition",
            "title": "Daily Glucose Pattern Analysis",
            "insight": daily_patterns["insight"],
            "confidence": daily_patterns["confidence"],
            "action": daily_patterns["action"],
            "priority": "medium"
        })

    # 2. Meal-Glucose Correlation Analysis
    meal_insights = _analyze_meal_glucose_correlation(glucose_readings, meals)
    if meal_insights:
        insights.extend(meal_insights)

    # 3. Activity Impact Analysis
    activity_insights = _analyze_activity_impact(glucose_readings, activities)
    if activity_insights:
        insights.extend(activity_insights)

    # 4. Insulin Sensitivity Analysis
    insulin_insights = _analyze_insulin_sensitivity(glucose_readings, insulin_doses)
    if insulin_insights:
        insights.extend(insulin_insights)

    # 5. Predictive Insights
    predictive_insights = _generate_predictive_insights(glucose_readings, current_user)
    if predictive_insights:
        insights.extend(predictive_insights)

    return insights

def _analyze_daily_patterns(glucose_readings: List[GlucoseReading]) -> Optional[Dict[str, Any]]:
    """Analyze daily glucose patterns to identify recurring trends."""
    if len(glucose_readings) < 7:  # Need at least a week of data
        return None

    # Group readings by hour of day
    hourly_patterns = defaultdict(list)
    for reading in glucose_readings:
        hour = reading.timestamp.hour
        hourly_patterns[hour].append(reading.value)

    # Find patterns
    high_hours = []
    low_hours = []

    for hour, values in hourly_patterns.items():
        if len(values) >= 3:  # Need at least 3 readings for pattern
            avg = sum(values) / len(values)
            if avg > 180:
                high_hours.append(hour)
            elif avg < 100:
                low_hours.append(hour)

    if high_hours and low_hours:
        return {
            "insight": f"Your glucose tends to be high around {', '.join(map(str, sorted(high_hours)))}:00 and low around {', '.join(map(str, sorted(low_hours)))}:00",
            "confidence": "high",
            "action": "Consider adjusting meal timing or insulin dosing during these hours"
        }
    elif high_hours:
        return {
            "insight": f"Your glucose tends to be elevated around {', '.join(map(str, sorted(high_hours)))}:00",
            "confidence": "medium",
            "action": "Monitor your routine during these hours and consider preventive measures"
        }
    elif low_hours:
        return {
            "insight": f"Your glucose tends to be lower around {', '.join(map(str, sorted(low_hours)))}:00",
            "confidence": "medium",
            "action": "Be prepared for potential hypoglycemia during these hours"
        }

    return None

def _analyze_meal_glucose_correlation(glucose_readings: List[GlucoseReading], meals: List[Meal]) -> List[Dict[str, Any]]:
    """Analyze correlation between meals and glucose changes."""
    insights = []

    if not meals or len(glucose_readings) < 5:
        return insights

    # Analyze meal timing and glucose response
    meal_glucose_pairs = []
    for meal in meals:
        # Find glucose readings before and after meal
        pre_meal = None
        post_meal = None

        for reading in glucose_readings:
            time_diff = (reading.timestamp - meal.timestamp).total_seconds() / 60

            if -30 <= time_diff <= 0 and pre_meal is None:
                pre_meal = reading.value
            elif 0 <= time_diff <= 120 and post_meal is None:
                post_meal = reading.value

        if pre_meal and post_meal:
            meal_glucose_pairs.append({
                "meal_carbs": meal.total_carbs or 0,
                "glucose_change": post_meal - pre_meal,
                "meal_time": meal.timestamp.hour
            })

    if len(meal_glucose_pairs) >= 3:
        # Analyze carb sensitivity
        carb_sensitivity = []
        for pair in meal_glucose_pairs:
            if pair["meal_carbs"] > 0:
                sensitivity = pair["glucose_change"] / pair["meal_carbs"]
                carb_sensitivity.append(sensitivity)

        if carb_sensitivity:
            avg_sensitivity = sum(carb_sensitivity) / len(carb_sensitivity)

            if avg_sensitivity > 3:
                insights.append({
                    "type": "meal_analysis",
                    "title": "High Carb Sensitivity Detected",
                    "insight": f"Your glucose increases by {avg_sensitivity:.1f} mg/dl per gram of carbs",
                    "confidence": "high",
                    "action": "Consider reducing carb portions or adjusting insulin-to-carb ratio",
                    "priority": "high"
                })
            elif avg_sensitivity < 1:
                insights.append({
                    "type": "meal_analysis",
                    "title": "Low Carb Sensitivity Detected",
                    "insight": f"Your glucose increases by {avg_sensitivity:.1f} mg/dl per gram of carbs",
                    "confidence": "medium",
                    "action": "You may be able to handle more carbs or need less insulin",
                    "priority": "medium"
                })

    return insights

def _analyze_activity_impact(glucose_readings: List[GlucoseReading], activities: List[Activity]) -> List[Dict[str, Any]]:
    """Analyze the impact of activities on glucose levels."""
    insights = []

    if not activities or len(glucose_readings) < 5:
        return insights

    # Analyze activity types and glucose response
    activity_glucose_pairs = []
    for activity in activities:
        # Find glucose readings before and after activity
        pre_activity = None
        post_activity = None

        for reading in glucose_readings:
            time_diff = (reading.timestamp - activity.timestamp).total_seconds() / 60

            if -30 <= time_diff <= 0 and pre_activity is None:
                pre_activity = reading.value
            elif 0 <= time_diff <= 120 and post_activity is None:
                post_activity = reading.value

        if pre_activity and post_activity:
            activity_glucose_pairs.append({
                "activity_type": activity.type,
                "intensity": activity.intensity,
                "duration": activity.duration_min or 0,
                "glucose_change": post_activity - pre_activity
            })

    if len(activity_glucose_pairs) >= 3:
        # Group by activity type
        activity_impacts = defaultdict(list)
        for pair in activity_glucose_pairs:
            activity_impacts[pair["activity_type"]].append(pair["glucose_change"])

        for activity_type, changes in activity_impacts.items():
            if len(changes) >= 2:
                avg_change = sum(changes) / len(changes)

                if avg_change < -20:
                    insights.append({
                        "type": "activity_analysis",
                        "title": f"{activity_type.title()} Lowers Your Glucose",
                        "insight": f"{activity_type} typically lowers your glucose by {abs(avg_change):.0f} mg/dl",
                        "confidence": "high",
                        "action": "Consider reducing insulin or eating a snack before this activity",
                        "priority": "medium"
                    })
                elif avg_change > 20:
                    insights.append({
                        "type": "activity_analysis",
                        "title": f"{activity_type.title()} Raises Your Glucose",
                        "insight": f"{activity_type} typically raises your glucose by {avg_change:.0f} mg/dl",
                        "confidence": "medium",
                        "action": "Monitor glucose closely during this activity",
                        "priority": "medium"
                    })

    return insights

def _analyze_insulin_sensitivity(glucose_readings: List[GlucoseReading], insulin_doses: List[InsulinDose]) -> List[Dict[str, Any]]:
    """Analyze insulin sensitivity patterns."""
    insights = []

    if not insulin_doses or len(glucose_readings) < 5:
        return insights

    # Analyze insulin effectiveness
    insulin_glucose_pairs = []
    for dose in insulin_doses:
        # Find glucose readings before and after insulin
        pre_insulin = None
        post_insulin = None

        for reading in glucose_readings:
            time_diff = (reading.timestamp - dose.timestamp).total_seconds() / 60

            if -30 <= time_diff <= 0 and pre_insulin is None:
                pre_insulin = reading.value
            elif 0 <= time_diff <= 180 and post_insulin is None:
                post_insulin = reading.value

        if pre_insulin and post_insulin:
            insulin_glucose_pairs.append({
                "insulin_units": dose.units,
                "glucose_change": post_insulin - pre_insulin,
                "insulin_time": dose.timestamp.hour
            })

    if len(insulin_glucose_pairs) >= 3:
        # Calculate insulin sensitivity
        sensitivities = []
        for pair in insulin_glucose_pairs:
            if pair["insulin_units"] > 0:
                sensitivity = pair["glucose_change"] / pair["insulin_units"]
                sensitivities.append(sensitivity)

        if sensitivities:
            avg_sensitivity = sum(sensitivities) / len(sensitivities)

            if avg_sensitivity > -10:
                insights.append({
                    "type": "insulin_analysis",
                    "title": "Low Insulin Sensitivity",
                    "insight": f"Your insulin sensitivity is {abs(avg_sensitivity):.1f} mg/dl per unit",
                    "confidence": "high",
                    "action": "Consider discussing insulin resistance with your healthcare provider",
                    "priority": "high"
                })
            elif avg_sensitivity < -30:
                insights.append({
                    "type": "insulin_analysis",
                    "title": "High Insulin Sensitivity",
                    "insight": f"Your insulin sensitivity is {abs(avg_sensitivity):.1f} mg/dl per unit",
                    "confidence": "medium",
                    "action": "Be cautious with insulin dosing to avoid hypoglycemia",
                    "priority": "high"
                })

    return insights

def _generate_predictive_insights(glucose_readings: List[GlucoseReading], current_user: User) -> List[Dict[str, Any]]:
    """Generate predictive insights based on historical patterns."""
    insights = []

    if len(glucose_readings) < 10:  # Need significant historical data
        return insights

    # Analyze recent trends
    sorted_readings = sorted(glucose_readings, key=lambda x: x.timestamp)
    recent_readings = sorted_readings[-7:]  # Last 7 readings
    earlier_readings = sorted_readings[-14:-7]  # 7 readings before that

    if len(recent_readings) >= 3 and len(earlier_readings) >= 3:
        recent_avg = sum(r.value for r in recent_readings) / len(recent_readings)
        earlier_avg = sum(r.value for r in earlier_readings) / len(earlier_readings)

        trend = recent_avg - earlier_avg

        if trend > 30:
            insights.append({
                "type": "predictive",
                "title": "Rising Glucose Trend",
                "insight": "Your glucose levels have been trending upward recently",
                "confidence": "medium",
                "action": "Review your recent routine changes and consider preventive measures",
                "priority": "medium"
            })
        elif trend < -30:
            insights.append({
                "type": "predictive",
                "title": "Falling Glucose Trend",
                "insight": "Your glucose levels have been trending downward recently",
                "confidence": "medium",
                "action": "Monitor for hypoglycemia and consider adjusting insulin doses",
                "priority": "medium"
            })

    # Predict potential issues based on patterns
    glucose_values = [r.value for r in glucose_readings]
    if len(glucose_values) >= 5:
        recent_high_count = sum(1 for v in glucose_values[-5:] if v > 200)
        recent_low_count = sum(1 for v in glucose_values[-5:] if v < 70)

        if recent_high_count >= 3:
            insights.append({
                "type": "predictive",
                "title": "High Glucose Pattern",
                "insight": "You've had high glucose readings in 3+ of your last 5 measurements",
                "confidence": "high",
                "action": "Consider reviewing your meal planning and insulin dosing",
                "priority": "high"
            })
        elif recent_low_count >= 2:
            insights.append({
                "type": "predictive",
                "title": "Low Glucose Pattern",
                "insight": "You've had low glucose readings in 2+ of your last 5 measurements",
                "confidence": "high",
                "action": "Be prepared for hypoglycemia and consider reducing insulin doses",
                "priority": "high"
            })

    return insights
