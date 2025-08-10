from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.insulin_dose import InsulinDose
from app.models.user import User
from app.schemas import (
    InsulinDoseCreate, InsulinDoseUpdate, InsulinDoseReadBasic, InsulinDoseReadDetail
)
from app.core.security import get_current_user
from typing import List
from datetime import datetime, UTC

router = APIRouter(prefix="/insulin-doses", tags=["insulin-doses"])

def can_edit_insulin_dose(dose: InsulinDose, user: User) -> bool:
    return dose.user_id == user.id or user.is_admin

# Create a new insulin dose
@router.post("/", response_model=InsulinDoseReadDetail, status_code=status.HTTP_201_CREATED)
def create_insulin_dose(dose_in: InsulinDoseCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Ensure the user is authenticated and get their ID
    assert current_user.id is not None, "User ID must not be None"
    # Create a new InsulinDose object with the provided data
    dose = InsulinDose(
        user_id=int(current_user.id),
        units=dose_in.units,
        timestamp=dose_in.timestamp or datetime.now(UTC),
        note=dose_in.note,
        meal_context=getattr(dose_in, 'meal_context', None),
        type=getattr(dose_in, 'type', None)
    )
    # Add and save the new dose to the database
    session.add(dose)
    session.commit()
    session.refresh(dose)  # Get the latest data (including the new ID)
    return InsulinDoseReadDetail.model_validate(dose)

# List all insulin doses for the current user (or all if admin)
@router.get("/", response_model=List[InsulinDoseReadBasic])
def list_insulin_doses(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Admins see all doses, users see only their own
    if current_user.is_admin:
        doses = session.exec(select(InsulinDose)).all()
    else:
        doses = session.exec(select(InsulinDose).where(InsulinDose.user_id == current_user.id)).all()
    # Return a list of dose summaries
    return [InsulinDoseReadBasic.model_validate(d) for d in doses]

# Get a single insulin dose by ID
@router.get("/{dose_id}", response_model=InsulinDoseReadDetail)
def get_insulin_dose(dose_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Fetch the dose from the database
    dose = session.get(InsulinDose, dose_id)
    if not dose:
        raise HTTPException(status_code=404, detail="InsulinDose not found")
    # Only the owner or admin can view
    if not can_edit_insulin_dose(dose, current_user) and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return InsulinDoseReadDetail.model_validate(dose)

# Update an existing insulin dose
@router.put("/{dose_id}", response_model=InsulinDoseReadDetail)
def update_insulin_dose(dose_id: int, dose_in: InsulinDoseUpdate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Fetch the dose from the database
    dose = session.get(InsulinDose, dose_id)
    if not dose:
        raise HTTPException(status_code=404, detail="InsulinDose not found")
    # Only the owner or admin can update
    if not can_edit_insulin_dose(dose, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    # Update fields with new values
    for field, value in dose_in.model_dump(exclude_unset=True).items():
        setattr(dose, field, value)
    session.commit()
    session.refresh(dose)
    return InsulinDoseReadDetail.model_validate(dose)

# Delete an insulin dose
@router.delete("/{dose_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_insulin_dose(dose_id: int, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    # Fetch the dose from the database
    dose = session.get(InsulinDose, dose_id)
    if not dose:
        raise HTTPException(status_code=404, detail="InsulinDose not found")
    # Only the owner or admin can delete
    if not can_edit_insulin_dose(dose, current_user):
        raise HTTPException(status_code=403, detail="Not authorized")
    # Delete the dose from the database
    session.delete(dose)
    session.commit()
    return None