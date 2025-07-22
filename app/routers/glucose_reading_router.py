from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.glucose_reading import GlucoseReading
from app.models.user import User
from app.schemas import (
    GlucoseReadingCreate, GlucoseReadingUpdate, GlucoseReadingReadBasic, GlucoseReadingReadDetail
)
from app.core.security import get_current_user
from typing import List
from datetime import datetime

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
        timestamp=reading_in.timestamp or datetime.utcnow(),
        note=reading_in.note
    )
    # Add and save the new reading to the database
    session.add(reading)
    session.commit()
    session.refresh(reading)  # Get the latest data (including the new ID)
    return GlucoseReadingReadDetail.from_orm(reading)

# List all glucose readings for the current user (or all if admin)
@router.get("/", response_model=List[GlucoseReadingReadBasic])
def list_glucose_readings(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Admins see all readings, users see only their own
    if current_user.is_admin:
        readings = session.exec(select(GlucoseReading)).all()
    else:
        readings = session.exec(select(GlucoseReading).where(GlucoseReading.user_id == current_user.id)).all()
    # Return a list of reading summaries
    return [GlucoseReadingReadBasic.from_orm(r) for r in readings]

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
    return GlucoseReadingReadDetail.from_orm(reading)

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
    for field, value in reading_in.dict(exclude_unset=True).items():
        setattr(reading, field, value)
    session.commit()
    session.refresh(reading)
    return GlucoseReadingReadDetail.from_orm(reading)

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