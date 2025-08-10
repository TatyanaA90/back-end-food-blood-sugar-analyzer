from fastapi import HTTPException, status

_UNIT_MAP = {
    "mg/dl": "mg/dL",
    "mmol/l": "mmol/L",
}

def normalize_unit(unit: str) -> tuple[str, str]:
    """Validate and normalize glucose unit.

    Returns (canonical_unit, requested_unit).
    Accepts 'mg/dl' or 'mmol/l' (case-insensitive). Raises 400 otherwise.
    """
    requested = unit
    key = (unit or "").strip().lower()
    canonical = _UNIT_MAP.get(key)
    if not canonical:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid unit. Must be 'mg/dl' or 'mmol/l'",
        )
    return canonical, requested


