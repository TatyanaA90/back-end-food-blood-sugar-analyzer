from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.glucose_reading import GlucoseReading
from app.models.user import User
from app.schemas import (
    GlucoseReadingCreate, GlucoseReadingUpdate, GlucoseReadingReadBasic, GlucoseReadingReadDetail
)
from app.core.security import get_current_user
from typing import List
from datetime import datetime, UTC

router = APIRouter(prefix="/glucose-readings", tags=["glucose-readings"])

def can_edit_glucose_reading(reading: GlucoseReading, user: User) -> bool:
    return reading.user_id == user.id or user.is_admin

# Create a new glucose reading
@router.post("/", response_model=GlucoseReadingReadDetail, status_code=status.HTTP_201_CREATED)
def create_glucose_reading(reading_in: GlucoseReadingCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Ensure the user is authenticated and get their ID
    assert current_user.id is not None, "User ID must not be None"
    # Create a new GlucoseReading object with the provided data
    reading = GlucoseReading(
        user_id=int(current_user.id),
        value=reading_in.value,
        unit=reading_in.unit,  # User can choose "mg/dl" or "mmol/l"
        timestamp=reading_in.timestamp or datetime.now(UTC),
        meal_context=reading_in.meal_context,
        note=reading_in.note
    )
    # Add and save the new reading to the database
    session.add(reading)
    session.commit()
    session.refresh(reading)  # Get the latest data (including the new ID)
    return GlucoseReadingReadDetail.model_validate(reading)

# List all glucose readings for the current user (or all if admin)
@router.get("/", response_model=List[GlucoseReadingReadBasic])
def list_glucose_readings(
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    start_datetime: datetime | None = Query(None, description="Start datetime (ISO 8601, UTC preferred)"),
    end_datetime: datetime | None = Query(None, description="End datetime (ISO 8601, UTC preferred)"),
    meal_context: str | None = Query(None),
    unit: str | None = Query(None),
    search: str | None = Query(None),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Build the base query
    query = select(GlucoseReading)

    # Filter by user (unless admin)
    if not current_user.is_admin:
        query = query.where(GlucoseReading.user_id == current_user.id)

    # Apply filters
    if start_datetime:
        sdt = start_datetime if start_datetime.tzinfo else start_datetime.replace(tzinfo=UTC)
        query = query.where(GlucoseReading.timestamp >= sdt)
    if end_datetime:
        edt = end_datetime if end_datetime.tzinfo else end_datetime.replace(tzinfo=UTC)
        query = query.where(GlucoseReading.timestamp <= edt)
    if start_date and not start_datetime:
        try:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.where(GlucoseReading.timestamp >= start_dt)
        except ValueError:
            pass  # Ignore invalid date format

    if end_date and not end_datetime:
        try:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.where(GlucoseReading.timestamp <= end_dt)
        except ValueError:
            pass  # Ignore invalid date format

    if meal_context:
        query = query.where(GlucoseReading.meal_context == meal_context)

    if unit:
        query = query.where(GlucoseReading.unit == unit)

    if search:
        search_term = f"%{search}%"
        query = query.where(
            (GlucoseReading.value.cast(str).contains(search_term)) |
            (GlucoseReading.unit.contains(search_term)) |
            (GlucoseReading.meal_context.contains(search_term)) |
            (GlucoseReading.note.contains(search_term))
        )

    # Execute query and return results
    readings = session.exec(query).all()
    return [GlucoseReadingReadBasic.model_validate(r) for r in readings]

# Get a single glucose reading by ID
@router.get("/{reading_id}", response_model=GlucoseReadingReadDetail)
def get_glucose_reading(reading_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Fetch the reading from the database
    reading = session.get(GlucoseReading, reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail="GlucoseReading not found")
    # Only the owner or admin can view
    if not can_edit_glucose_reading(reading, current_user) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return GlucoseReadingReadDetail.model_validate(reading)

# Update an existing glucose reading
@router.put("/{reading_id}", response_model=GlucoseReadingReadDetail)
def update_glucose_reading(reading_id: int, reading_in: GlucoseReadingUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Fetch the reading from the database
    reading = session.get(GlucoseReading, reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail="GlucoseReading not found")
    # Only the owner or admin can update
    if not can_edit_glucose_reading(reading, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    # Update fields with new values
    for field, value in reading_in.model_dump(exclude_unset=True).items():
        setattr(reading, field, value)
    session.commit()
    session.refresh(reading)
    return GlucoseReadingReadDetail.model_validate(reading)

# Delete a glucose reading
@router.delete("/{reading_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_glucose_reading(reading_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Fetch the reading from the database
    reading = session.get(GlucoseReading, reading_id)
    if not reading:
        raise HTTPException(status_code=404, detail="GlucoseReading not found")
    # Only the owner or admin can delete
    if not can_edit_glucose_reading(reading, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    # Delete the reading from the database
    session.delete(reading)
    session.commit()
    return None