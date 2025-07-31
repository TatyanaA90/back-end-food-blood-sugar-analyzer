from fastapi import APIRouter, Depends, Query, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.core.security import get_current_user
from app.models.user import User
from app.models.glucose_reading import GlucoseReading
from app.models.meal import Meal
from app.models.activity import Activity
from app.models.insulin_dose import InsulinDose
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta, UTC
import statistics
from collections import defaultdict

router = APIRouter(prefix="/visualization", tags=["visualization"])

def convert_glucose_value(value: float, from_unit: str, to_unit: str) -> float:
    """
    Convert glucose values between mg/dl and mmol/l.
    mg/dl to mmol/l: divide by 18
    mmol/l to mg/dl: multiply by 18
    """
    if from_unit == to_unit:
        return value
    
    if from_unit == "mg/dl" and to_unit == "mmol/l":
        return round(value / 18, 1)
    elif from_unit == "mmol/l" and to_unit == "mg/dl":
        return round(value * 18, 0)
    else:
        raise ValueError(f"Unsupported unit conversion: {from_unit} to {to_unit}")

def get_glucose_readings_for_window(
    current_user: User, 
    window: str, 
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[GlucoseReading]:
    """Get glucose readings for the specified time window."""
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

    query = select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)
    if start:
        query = query.where(GlucoseReading.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(GlucoseReading.timestamp <= datetime.combine(end, datetime.max.time()))
    
    readings = session.exec(query).all()
    return [r for r in readings if r.value is not None and r.timestamp is not None]

def get_meals_for_window(
    current_user: User, 
    window: str, 
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Meal]:
    """Get meals for the specified time window."""
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

    query = select(Meal).where(Meal.user_id == current_user.id)
    if start:
        query = query.where(Meal.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(Meal.timestamp <= datetime.combine(end, datetime.max.time()))
    
    return session.exec(query).all()

def get_activities_for_window(
    current_user: User, 
    window: str, 
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[Activity]:
    """Get activities for the specified time window."""
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

    query = select(Activity).where(Activity.user_id == current_user.id)
    if start:
        query = query.where(Activity.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(Activity.timestamp <= datetime.combine(end, datetime.max.time()))
    
    return session.exec(query).all()

def get_insulin_doses_for_window(
    current_user: User, 
    window: str, 
    session: Session,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
) -> List[InsulinDose]:
    """Get insulin doses for the specified time window."""
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

    query = select(InsulinDose).where(InsulinDose.user_id == current_user.id)
    if start:
        query = query.where(InsulinDose.timestamp >= datetime.combine(start, datetime.min.time()))
    if end:
        query = query.where(InsulinDose.timestamp <= datetime.combine(end, datetime.max.time()))
    
    return session.exec(query).all()

def calculate_glucose_summary(glucose_readings: List[GlucoseReading], target_unit: str = "mg/dl") -> Dict[str, Any]:
    """Calculate glucose summary with unit conversion support."""
    if not glucose_readings:
        return {
            "current_value": None,
            "trend": "no_data",
            "last_reading_time": None,
            "data_source": None,
            "unit": target_unit
        }
    
    # Sort by timestamp
    sorted_readings = sorted(glucose_readings, key=lambda r: r.timestamp)
    latest_reading = sorted_readings[-1]
    
    # Convert to target unit
    current_value = convert_glucose_value(latest_reading.value, latest_reading.unit, target_unit)
    
    # Calculate trend (last 3 readings)
    if len(sorted_readings) >= 3:
        recent_values = [r.value for r in sorted_readings[-3:]]
        if recent_values[-1] > recent_values[0]:
            trend = "rising"
        elif recent_values[-1] < recent_values[0]:
            trend = "falling"
        else:
            trend = "stable"
    else:
        trend = "insufficient_data"
    
    return {
        "current_value": current_value,
        "trend": trend,
        "last_reading_time": latest_reading.timestamp.isoformat(),
        "data_source": "csv_upload" if latest_reading.note and "csv" in latest_reading.note.lower() else "manual_entry",
        "unit": target_unit
    }

def format_recent_meals(meals: List[Meal], limit: int = 5) -> List[Dict[str, Any]]:
    """Format recent meals for dashboard display."""
    sorted_meals = sorted(meals, key=lambda m: m.timestamp, reverse=True)[:limit]
    
    formatted_meals = []
    for meal in sorted_meals:
        formatted_meal = {
            "timestamp": meal.timestamp.isoformat(),
            "description": meal.description or "Meal",
            "total_carbs": meal.total_carbs,
            "total_weight": meal.total_weight,
            "ingredients_count": len(meal.ingredients) if hasattr(meal, 'ingredients') else 0,
            "photo_url": meal.photo_url,
            "note": meal.note
        }
        formatted_meals.append(formatted_meal)
    
    return formatted_meals

def format_upcoming_insulin(insulin_doses: List[InsulinDose], limit: int = 5) -> List[Dict[str, Any]]:
    """Format upcoming insulin doses for dashboard display."""
    # Filter future doses (within next 24 hours)
    now = datetime.now(UTC)
    future_doses = [
        dose for dose in insulin_doses 
        if dose.timestamp and dose.timestamp > now and dose.timestamp <= now + timedelta(days=1)
    ]
    
    sorted_doses = sorted(future_doses, key=lambda d: d.timestamp)[:limit]
    
    formatted_doses = []
    for dose in sorted_doses:
        formatted_dose = {
            "scheduled_time": dose.timestamp.isoformat(),
            "units": dose.units,
            "type": dose.type or "rapid_acting",
            "related_meal": dose.related_meal.description if dose.related_meal else None,
            "note": dose.note
        }
        formatted_doses.append(formatted_dose)
    
    return formatted_doses

def calculate_activity_summary(activities: List[Activity]) -> Dict[str, Any]:
    """Calculate activity summary for dashboard."""
    if not activities:
        return {
            "total_activities": 0,
            "total_calories_burned": 0,
            "most_common_type": None,
            "average_duration": 0
        }
    
    total_calories = sum(a.calories_burned or 0 for a in activities)
    total_duration = sum(a.duration_min or 0 for a in activities)
    
    # Find most common activity type
    activity_types = [a.type for a in activities if a.type]
    most_common_type = max(set(activity_types), key=activity_types.count) if activity_types else None
    
    return {
        "total_activities": len(activities),
        "total_calories_burned": total_calories,
        "most_common_type": most_common_type,
        "average_duration": round(total_duration / len(activities), 1) if activities else 0
    }

def analyze_data_sources(
    glucose_readings: List[GlucoseReading],
    meals: List[Meal],
    activities: List[Activity],
    insulin_doses: List[InsulinDose]
) -> Dict[str, Any]:
    """Analyze data sources and completeness."""
    # Analyze glucose readings
    csv_uploaded = sum(1 for r in glucose_readings if r.note and "csv" in r.note.lower())
    manual_entries = len(glucose_readings) - csv_uploaded
    
    # Analyze meals
    with_ingredients = sum(1 for m in meals if hasattr(m, 'ingredients') and m.ingredients)
    with_photos = sum(1 for m in meals if m.photo_url)
    
    # Analyze activities
    with_calories = sum(1 for a in activities if a.calories_burned is not None)
    
    # Analyze insulin doses
    with_meal_relationships = sum(1 for i in insulin_doses if i.related_meal_id is not None)
    
    return {
        "glucose_readings": {
            "total_count": len(glucose_readings),
            "csv_uploaded": csv_uploaded,
            "manual_entries": manual_entries,
            "last_updated": glucose_readings[-1].timestamp.isoformat() if glucose_readings else None
        },
        "meals": {
            "total_count": len(meals),
            "with_ingredients": with_ingredients,
            "with_photos": with_photos
        },
        "activities": {
            "total_count": len(activities),
            "with_calorie_calculations": with_calories
        },
        "insulin_doses": {
            "total_count": len(insulin_doses),
            "with_meal_relationships": with_meal_relationships
        }
    }

@router.get("/dashboard")
def get_dashboard_overview(
    window: str = Query("week", description="Time window: day, week, month, 3months, custom"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    unit: str = Query("mg/dl", description="Unit for glucose values: 'mg/dl' or 'mmol/l'"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns comprehensive dashboard data using existing glucose readings, meals, activities, and insulin doses.
    Works with CSV-uploaded and manually entered data.
    Supports unit conversion between mg/dl and mmol/l.
    """
    # Validate unit parameter
    if unit not in ["mg/dl", "mmol/l"]:
        raise HTTPException(status_code=400, detail="Unit must be 'mg/dl' or 'mmol/l'")
    
    # Get data for the specified window
    glucose_readings = get_glucose_readings_for_window(current_user, window, session, start_date, end_date)
    meals = get_meals_for_window(current_user, window, session, start_date, end_date)
    activities = get_activities_for_window(current_user, window, session, start_date, end_date)
    insulin_doses = get_insulin_doses_for_window(current_user, window, session, start_date, end_date)
    
    # Calculate dashboard components
    glucose_summary = calculate_glucose_summary(glucose_readings, unit)
    recent_meals = format_recent_meals(meals)
    upcoming_insulin = format_upcoming_insulin(insulin_doses)
    activity_summary = calculate_activity_summary(activities)
    data_sources = analyze_data_sources(glucose_readings, meals, activities, insulin_doses)
    
    return {
        "dashboard": {
            "glucose_summary": glucose_summary,
            "recent_meals": recent_meals,
            "upcoming_insulin": upcoming_insulin,
            "activity_summary": activity_summary
        },
        "data_sources": data_sources,
        "meta": {
            "window": window,
            "unit": unit,
            "generated_at": datetime.now(UTC).isoformat()
        }
    }

@router.get("/glucose-timeline")
def get_glucose_timeline(
    window: str = Query("week"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    include_events: bool = Query(True, description="Include meals, activities, insulin"),
    include_ingredients: bool = Query(False, description="Include meal ingredients"),
    unit: str = Query("mg/dl", description="Unit for glucose values: 'mg/dl' or 'mmol/l'"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns glucose readings with overlaid events for timeline visualization.
    Uses existing data structure from glucose readings, meals, activities, and insulin doses.
    Supports unit conversion between mg/dl and mmol/l.
    Frontend should handle timeline styling and event display.
    """
    # Validate unit parameter
    if unit not in ["mg/dl", "mmol/l"]:
        raise HTTPException(status_code=400, detail="Unit must be 'mg/dl' or 'mmol/l'")
    
    # Get data for the specified window
    glucose_readings = get_glucose_readings_for_window(current_user, window, session, start_date, end_date)
    meals = get_meals_for_window(current_user, window, session, start_date, end_date)
    activities = get_activities_for_window(current_user, window, session, start_date, end_date)
    insulin_doses = get_insulin_doses_for_window(current_user, window, session, start_date, end_date)
    
    # Format glucose readings with unit conversion
    formatted_readings = []
    for reading in glucose_readings:
        converted_value = convert_glucose_value(reading.value, reading.unit, unit)
        formatted_readings.append({
            "timestamp": reading.timestamp.isoformat(),
            "value": converted_value,
            "unit": unit,
            "source": "csv_upload" if reading.note and "csv" in reading.note.lower() else "manual_entry",
            "note": reading.note
        })
    
    # Format events if requested
    events = []
    if include_events:
        # Add meals
        for meal in meals:
            event = {
                "timestamp": meal.timestamp.isoformat(),
                "type": "meal",
                "description": meal.description or "Meal",
                "total_carbs": meal.total_carbs,
                "total_weight": meal.total_weight,
                "photo_url": meal.photo_url,
                "note": meal.note
            }
            if include_ingredients and hasattr(meal, 'ingredients'):
                event["ingredients"] = [
                    {
                        "name": ing.name,
                        "carbs": ing.carbs,
                        "weight": ing.weight
                    } for ing in meal.ingredients
                ]
            events.append(event)
        
        # Add insulin doses
        for insulin in insulin_doses:
            event = {
                "timestamp": insulin.timestamp.isoformat(),
                "type": "insulin_dose",
                "units": insulin.units,
                "insulin_type": insulin.type or "rapid_acting",
                "related_meal": insulin.related_meal.description if insulin.related_meal else None,
                "note": insulin.note
            }
            events.append(event)
        
        # Add activities
        for activity in activities:
            event = {
                "timestamp": activity.timestamp.isoformat(),
                "type": "activity",
                "activity_type": activity.type,
                "duration_minutes": activity.duration_min,
                "calories_burned": activity.calories_burned,
                "intensity": activity.intensity,
                "note": activity.note
            }
            events.append(event)
    
    # Sort events by timestamp
    events.sort(key=lambda x: x["timestamp"])
    
    return {
        "glucose_readings": formatted_readings,
        "events": events,
        "meta": {
            "window": window,
            "unit": unit,
            "total_glucose_readings": len(formatted_readings),
            "total_events": len(events),
            "generated_at": datetime.now(UTC).isoformat()
        }
    }

@router.get("/meal-impact-data")
def get_meal_impact_data(
    window: str = Query("week"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    group_by: str = Query("time_of_day", description="Group by 'meal_type' or 'time_of_day'"),
    unit: str = Query("mg/dl", description="Unit for glucose values: 'mg/dl' or 'mmol/l'"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns meal impact data for visualization.
    Uses existing meal and glucose data with unit conversion support.
    Frontend should handle chart styling and display.
    """
    # Validate unit parameter
    if unit not in ["mg/dl", "mmol/l"]:
        raise HTTPException(status_code=400, detail="Unit must be 'mg/dl' or 'mmol/l'")
    
    # Get data for the specified window
    glucose_readings = get_glucose_readings_for_window(current_user, window, session, start_date, end_date)
    meals = get_meals_for_window(current_user, window, session, start_date, end_date)
    
    if not meals:
        return {
            "meal_impacts": [],
            "meta": {
                "window": window,
                "unit": unit,
                "message": "No meals found for the specified period"
            }
        }
    
    # Group meals by time of day or meal type
    meal_groups = defaultdict(list)
    
    for meal in meals:
        if meal.timestamp:
            meal_time = meal.timestamp
            
            if group_by == "time_of_day":
                hour = meal_time.hour
                if 5 <= hour < 11:
                    group = "breakfast"
                elif 11 <= hour < 16:
                    group = "lunch"
                elif 16 <= hour < 21:
                    group = "dinner"
                else:
                    group = "snack"
            else:  # meal_type
                group = meal.description.lower() if meal.description else "meal"
                # Simplify meal types
                if any(word in group for word in ["breakfast", "morning"]):
                    group = "breakfast"
                elif any(word in group for word in ["lunch", "noon", "midday"]):
                    group = "lunch"
                elif any(word in group for word in ["dinner", "evening", "night"]):
                    group = "dinner"
                else:
                    group = "snack"
            
            meal_groups[group].append(meal)
    
    # Calculate impact for each group
    meal_impacts = []
    
    for group, group_meals in meal_groups.items():
        total_glucose_change = 0
        meals_with_glucose = 0
        
        for meal in group_meals:
            if meal.timestamp:
                meal_time = meal.timestamp
                
                # Find glucose reading before meal (within 30 minutes)
                before_readings = [
                    r for r in glucose_readings 
                    if r.timestamp and 
                    meal_time - timedelta(minutes=30) <= r.timestamp <= meal_time
                ]
                
                # Find glucose reading after meal (within 2 hours)
                after_readings = [
                    r for r in glucose_readings 
                    if r.timestamp and 
                    meal_time <= r.timestamp <= meal_time + timedelta(hours=2)
                ]
                
                if before_readings and after_readings:
                    before_value = convert_glucose_value(before_readings[-1].value, before_readings[-1].unit, unit)
                    after_value = convert_glucose_value(after_readings[-1].value, after_readings[-1].unit, unit)
                    
                    glucose_change = after_value - before_value
                    total_glucose_change += glucose_change
                    meals_with_glucose += 1
        
        if meals_with_glucose > 0:
            avg_glucose_change = total_glucose_change / meals_with_glucose
            meal_impacts.append({
                "group": group,
                "avg_glucose_change": round(avg_glucose_change, 1),
                "num_meals": meals_with_glucose,
                "total_meals_in_group": len(group_meals)
            })
    
    return {
        "meal_impacts": meal_impacts,
        "meta": {
            "window": window,
            "unit": unit,
            "group_by": group_by,
            "total_meals_analyzed": len(meals),
            "generated_at": datetime.now(UTC).isoformat()
        }
    }

@router.get("/activity-impact-data")
def get_activity_impact_data(
    window: str = Query("week"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    group_by: str = Query("activity_type", description="Group by 'activity_type' or 'intensity'"),
    unit: str = Query("mg/dl", description="Unit for glucose values: 'mg/dl' or 'mmol/l'"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns activity impact data for visualization.
    Uses existing activity and glucose data with unit conversion support.
    Frontend should handle chart styling and display.
    """
    # Validate unit parameter
    if unit not in ["mg/dl", "mmol/l"]:
        raise HTTPException(status_code=400, detail="Unit must be 'mg/dl' or 'mmol/l'")
    
    # Get data for the specified window
    glucose_readings = get_glucose_readings_for_window(current_user, window, session, start_date, end_date)
    activities = get_activities_for_window(current_user, window, session, start_date, end_date)
    
    if not activities:
        return {
            "activity_impacts": [],
            "meta": {
                "window": window,
                "unit": unit,
                "message": "No activities found for the specified period"
            }
        }
    
    # Group activities by type or intensity
    activity_groups = defaultdict(list)
    
    for activity in activities:
        if group_by == "activity_type":
            group = activity.type
        else:  # intensity
            group = activity.intensity or "unknown"
        
        activity_groups[group].append(activity)
    
    # Calculate impact for each group
    activity_impacts = []
    
    for group, group_activities in activity_groups.items():
        total_glucose_change = 0
        activities_with_glucose = 0
        total_calories = 0
        total_duration = 0
        
        for activity in group_activities:
            if activity.timestamp:
                activity_time = activity.timestamp
                
                # Find glucose reading before activity (within 30 minutes)
                before_readings = [
                    r for r in glucose_readings 
                    if r.timestamp and 
                    activity_time - timedelta(minutes=30) <= r.timestamp <= activity_time
                ]
                
                # Find glucose reading after activity (within 2 hours)
                after_readings = [
                    r for r in glucose_readings 
                    if r.timestamp and 
                    activity_time <= r.timestamp <= activity_time + timedelta(hours=2)
                ]
                
                if before_readings and after_readings:
                    before_value = convert_glucose_value(before_readings[-1].value, before_readings[-1].unit, unit)
                    after_value = convert_glucose_value(after_readings[-1].value, after_readings[-1].unit, unit)
                    
                    glucose_change = after_value - before_value
                    total_glucose_change += glucose_change
                    activities_with_glucose += 1
                
                if activity.calories_burned:
                    total_calories += activity.calories_burned
                if activity.duration_min:
                    total_duration += activity.duration_min
        
        if activities_with_glucose > 0:
            avg_glucose_change = total_glucose_change / activities_with_glucose
            avg_calories = total_calories / len(group_activities) if group_activities else 0
            avg_duration = total_duration / len(group_activities) if group_activities else 0
            
            activity_impacts.append({
                "group": group,
                "avg_glucose_change": round(avg_glucose_change, 1),
                "num_activities": activities_with_glucose,
                "total_activities_in_group": len(group_activities),
                "avg_calories_burned": round(avg_calories, 1),
                "avg_duration_minutes": round(avg_duration, 1)
            })
    
    return {
        "activity_impacts": activity_impacts,
        "meta": {
            "window": window,
            "unit": unit,
            "group_by": group_by,
            "total_activities_analyzed": len(activities),
            "generated_at": datetime.now(UTC).isoformat()
        }
    }

@router.get("/glucose-trend-data")
def get_glucose_trend_data(
    window: str = Query("week"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    include_moving_average: bool = Query(True, description="Include moving average dataset"),
    moving_avg_window: int = Query(5, description="Window size for moving average"),
    unit: str = Query("mg/dl", description="Unit for glucose values: 'mg/dl' or 'mmol/l'"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Returns glucose trend data for visualization.
    Uses existing glucose readings data with unit conversion support.
    Frontend should handle styling and chart configuration.
    """
    # Validate unit parameter
    if unit not in ["mg/dl", "mmol/l"]:
        raise HTTPException(status_code=400, detail="Unit must be 'mg/dl' or 'mmol/l'")
    
    # Get glucose readings
    glucose_readings = get_glucose_readings_for_window(current_user, window, session, start_date, end_date)
    
    if not glucose_readings:
        return {
            "timestamps": [],
            "glucose_values": [],
            "moving_average": [],
            "meta": {
                "window": window,
                "unit": unit,
                "message": "No glucose readings found for the specified period"
            }
        }
    
    # Sort by timestamp
    sorted_readings = sorted(glucose_readings, key=lambda r: r.timestamp)
    
    timestamps = []
    glucose_values = []
    
    for reading in sorted_readings:
        timestamps.append(reading.timestamp.isoformat())
        
        # Convert to target unit
        converted_value = convert_glucose_value(reading.value, reading.unit, unit)
        glucose_values.append(converted_value)
    
    # Calculate moving average if requested
    moving_average = []
    if include_moving_average and len(glucose_values) >= moving_avg_window:
        for i in range(moving_avg_window - 1, len(glucose_values)):
            avg = sum(glucose_values[i - moving_avg_window + 1:i + 1]) / moving_avg_window
            moving_average.append(round(avg, 1))
    
    return {
        "timestamps": timestamps,
        "glucose_values": glucose_values,
        "moving_average": moving_average,
        "meta": {
            "window": window,
            "unit": unit,
            "total_readings": len(glucose_values),
            "moving_avg_window": moving_avg_window if moving_average else None,
            "generated_at": datetime.now(UTC).isoformat()
        }
    }

@router.get("/data-quality")
def get_data_quality_metrics(
    window: str = Query("month"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Shows data quality metrics and source distribution.
    Analyzes existing data completeness and consistency.
    """
    # Get data for the specified window
    glucose_readings = get_glucose_readings_for_window(current_user, window, session, start_date, end_date)
    meals = get_meals_for_window(current_user, window, session, start_date, end_date)
    activities = get_activities_for_window(current_user, window, session, start_date, end_date)
    insulin_doses = get_insulin_doses_for_window(current_user, window, session, start_date, end_date)
    
    # Analyze glucose readings
    csv_uploaded = sum(1 for r in glucose_readings if r.note and "csv" in r.note.lower())
    manual_entries = len(glucose_readings) - csv_uploaded
    
    # Calculate data gaps (readings more than 2 hours apart)
    gaps_longer_than_2_hours = 0
    if len(glucose_readings) > 1:
        sorted_readings = sorted(glucose_readings, key=lambda r: r.timestamp)
        for i in range(1, len(sorted_readings)):
            time_diff = sorted_readings[i].timestamp - sorted_readings[i-1].timestamp
            if time_diff.total_seconds() > 7200:  # 2 hours in seconds
                gaps_longer_than_2_hours += 1
    
    # Analyze meals
    with_ingredients = sum(1 for m in meals if hasattr(m, 'ingredients') and m.ingredients)
    with_photos = sum(1 for m in meals if m.photo_url)
    
    # Calculate meal-glucose correlation
    meals_with_glucose = 0
    for meal in meals:
        if meal.timestamp:
            # Check if there are glucose readings within 30 minutes before and 2 hours after
            meal_time = meal.timestamp
            before_readings = [r for r in glucose_readings if r.timestamp and 
                             meal_time - timedelta(minutes=30) <= r.timestamp <= meal_time]
            after_readings = [r for r in glucose_readings if r.timestamp and 
                            meal_time <= r.timestamp <= meal_time + timedelta(hours=2)]
            if before_readings and after_readings:
                meals_with_glucose += 1
    
    # Analyze activities
    with_calories = sum(1 for a in activities if a.calories_burned is not None)
    activities_with_glucose = 0
    for activity in activities:
        if activity.timestamp:
            # Check if there are glucose readings within 30 minutes before and 2 hours after
            activity_time = activity.timestamp
            before_readings = [r for r in glucose_readings if r.timestamp and 
                             activity_time - timedelta(minutes=30) <= r.timestamp <= activity_time]
            after_readings = [r for r in glucose_readings if r.timestamp and 
                            activity_time <= r.timestamp <= activity_time + timedelta(hours=2)]
            if before_readings and after_readings:
                activities_with_glucose += 1
    
    # Analyze insulin doses
    with_meal_relationships = sum(1 for i in insulin_doses if i.related_meal_id is not None)
    insulin_with_glucose = sum(1 for i in insulin_doses if i.timestamp and 
                              any(r.timestamp and abs((r.timestamp - i.timestamp).total_seconds()) < 1800 
                                  for r in glucose_readings))  # 30 minutes
    
    # Calculate coverage percentage (assuming ideal: 1 reading per hour)
    if window == "day":
        ideal_readings = 24
    elif window == "week":
        ideal_readings = 168
    elif window == "month":
        ideal_readings = 720
    elif window == "3months":
        ideal_readings = 2160
    else:
        ideal_readings = len(glucose_readings)  # Custom window
    
    coverage_percentage = min(100, (len(glucose_readings) / ideal_readings) * 100) if ideal_readings > 0 else 0
    
    # Generate recommendations
    recommendations = []
    if coverage_percentage < 70:
        recommendations.append("Add more glucose readings for better analysis coverage")
    if csv_uploaded < len(glucose_readings) * 0.5:
        recommendations.append("Consider uploading more CSV data for continuous monitoring")
    if meals_with_glucose < len(meals) * 0.8:
        recommendations.append("Add glucose readings before and after meals for better correlation analysis")
    if activities_with_glucose < len(activities) * 0.5:
        recommendations.append("Log glucose readings around activities for better impact analysis")
    if with_photos < len(meals) * 0.3:
        recommendations.append("Add photos to more meals for better tracking")
    
    return {
        "data_quality": {
            "glucose_readings": {
                "total": len(glucose_readings),
                "csv_uploaded": csv_uploaded,
                "manual_entries": manual_entries,
                "coverage_percentage": round(coverage_percentage, 1),
                "gaps_longer_than_2_hours": gaps_longer_than_2_hours,
                "data_freshness": glucose_readings[-1].timestamp.isoformat() if glucose_readings else None,
                "unit_consistency": "mixed" if len(set(r.unit for r in glucose_readings)) > 1 else glucose_readings[0].unit if glucose_readings else None
            },
            "meals": {
                "total": len(meals),
                "with_ingredients": with_ingredients,
                "with_glucose_readings": meals_with_glucose,
                "with_photos": with_photos,
                "completeness": round((with_ingredients / len(meals)) * 100, 1) if meals else 0
            },
            "activities": {
                "total": len(activities),
                "with_glucose_readings": activities_with_glucose,
                "with_calorie_calculations": with_calories,
                "completeness": round((with_calories / len(activities)) * 100, 1) if activities else 0
            },
            "insulin_doses": {
                "total": len(insulin_doses),
                "with_meal_relationships": with_meal_relationships,
                "with_glucose_readings": insulin_with_glucose,
                "completeness": round((with_meal_relationships / len(insulin_doses)) * 100, 1) if insulin_doses else 0
            }
        },
        "recommendations": recommendations,
        "meta": {
            "window": window,
            "generated_at": datetime.now(UTC).isoformat()
        }
    } 