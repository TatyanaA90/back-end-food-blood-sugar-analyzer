from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.glucose_reading import GlucoseReading
from app.models.user import User
from app.core.security import get_current_user
from typing import List
from datetime import datetime, UTC
import csv
import io

router = APIRouter(prefix="/cgm-upload", tags=["cgm-upload"])

@router.post("/", status_code=status.HTTP_201_CREATED)
async def upload_cgm_csv(
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # Read the uploaded file contents
    contents = await file.read()
    decoded = contents.decode("utf-8")
    # Use ';' as delimiter for this CSV format
    reader = csv.DictReader(io.StringIO(decoded), delimiter=';')
    imported = 0
    skipped = 0
    errors: List[str] = []
    for idx, row in enumerate(reader, start=1):
        try:
            # Validate required fields
            if not row.get("DAY") or not row.get("TIME") or not row.get("UDT_CGMS"):
                skipped += 1
                errors.append(f"Row {idx}: Missing DAY, TIME, or UDT_CGMS.")
                continue
            # Parse and validate value
            try:
                value = float(row["UDT_CGMS"])
            except Exception:
                skipped += 1
                errors.append(f"Row {idx}: Invalid UDT_CGMS value '{row['UDT_CGMS']}'.")
                continue
            # Combine DAY and TIME, parse as DD.MM.YYYY HH:MM
            try:
                dt_str = f"{row['DAY']} {row['TIME']}"
                # Treat CSV times as UTC to avoid browser-local shift on the client
                timestamp = datetime.strptime(dt_str, "%d.%m.%Y %H:%M").replace(tzinfo=UTC)
            except Exception:
                skipped += 1
                errors.append(f"Row {idx}: Invalid DAY/TIME '{dt_str}'.")
                continue
            unit = "mg/dl"  # Assume mg/dl
            note = row.get("REMARK")

            # Skip duplicates for the same user/timestamp
            existing = session.exec(
                select(GlucoseReading).where(
                    GlucoseReading.user_id == int(current_user.id),
                    GlucoseReading.timestamp == timestamp,
                )
            ).first()
            if existing:
                skipped += 1
                continue

            reading = GlucoseReading(
                user_id=int(current_user.id),
                value=value,
                unit=unit,
                timestamp=timestamp,
                note=note
            )
            session.add(reading)
            imported += 1
        except Exception as e:
            skipped += 1
            errors.append(f"Row {idx}: Unexpected error: {str(e)}")
    session.commit()
    return {
        "imported": imported,
        "skipped": skipped,
        "errors": errors
    }
