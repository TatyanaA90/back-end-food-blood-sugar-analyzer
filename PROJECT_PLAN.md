# Food & Blood Sugar Analyzer API Implementation Plan

## Stack
- FastAPI (Python)
- SQLModel
- PostgreSQL

## Rules
- All major architectural and process decisions must be summarized in CONVERSATION_SUMMARY.md as the project progresses. This file should be updated automatically to reflect key changes and agreements.

## Progress Checklist

- [x] Set up project: Git, virtual environment, install FastAPI, SQLModel, PostgreSQL driver, Alembic, etc.
- [x] Configure PostgreSQL database and environment variables.
- [x] Design and implement SQLModel models for User, GlucoseReading, Meal, MealIngredient, InsulinDose, Activity, ConditionLog, Goal.
- [x] Set up Alembic for database migrations.
- [x] Implement authentication and user management (registration, login, JWT, password hashing, username/password support).
- [x] Implement CRUD endpoints for Meals, including business logic (auto-calculate totals, permissions, cascade delete ingredients, admin/user access control, response models for list/detail).
- [x] Implement CRUD endpoints for Activities, including MET-based calories burned auto-calculation, weight tracking (kg/lb), permissions, and response models.
- [x] Implement CRUD endpoints for ConditionLogs, including standard business logic, permissions, and response models.
- [x] Implement CRUD endpoints for InsulinDoses, GlucoseReadings, including units for InsulinDose and value/unit for GlucoseReading.
- [x] Implement endpoint for CSV upload and parsing for CGM data, including semicolon-delimited files and mapping DAY/TIME/UDT_CGMS columns.
- [x] Implement analytics endpoints (core analytics completed).
    - [x] Implement /analytics/glucose-summary endpoint: returns summary statistics with optional grouping (day/week/month) or whole-range summary, supporting both basic stats and period-based analysis.
    - [x] Implement /analytics/glucose-trend endpoint: returns timestamped glucose readings for a selected timeframe (day, week, month, 3 months, custom), ready for line chart visualization. Supports optional moving average.
    - [x] Implement /analytics/agp-overlay endpoint: returns glucose values overlaid by time of day for AGP plot (median, percentiles, outliers).
    - [x] Implement /analytics/time-in-range endpoint: returns percent of time spent in low, target, and high glucose ranges for a selected period, for pie/stacked bar charts.
    - [x] Implement /analytics/glucose-variability endpoint: returns SD, CV, and GMI for selected timeframe, with plain-language explanations.
    - [ ] Implement /analytics/glucose-events endpoint: lists hypo/hyperglycemia events with start/end times and durations, for event timeline visualizations.
    - [ ] Implement /analytics/meal-impact endpoint: shows average glucose change after meals, by meal type or time of day, for before/after meal visualizations.
    - [ ] Implement /analytics/activity-impact endpoint: shows how exercise affects glucose, for before/after activity visualizations.
    - [ ] Implement /analytics/insulin-glucose-correlation endpoint: analyzes relationship between insulin doses and glucose changes, for scatter plot visualizations.
    - [ ] Implement /analytics/recommendations endpoint: provides actionable tips and alerts based on recent data and trends.
- [x] Write comprehensive tests for all endpoints.
    - [x] Create separate test files for each router/feature
    - [x] Implement TestClient-based API testing
    - [x] Add unique test data to prevent conflicts
    - [x] Test model validation and authentication
    - [x] Fix Pydantic V2 migration issues
    - [x] Fix datetime deprecation warnings
    - [x] Verify all 19 tests pass successfully
- [x] Code quality and maintenance improvements.
    - [x] Update to Pydantic V2 syntax (ConfigDict, model_validate, model_dump)
    - [x] Fix datetime.utcnow() deprecation warnings for Python 3.13 compatibility
    - [x] Update all imports to include UTC for timezone-aware datetime handling
    - [x] Ensure future-proof code following modern Python best practices
- [ ] Implement endpoints for visualization data (charts, timelines, metrics).
- [ ] Write tests for all endpoints.
- [ ] Document API with OpenAPI/Swagger (FastAPI auto-docs).
- [ ] (Optional) Deploy app (Docker, cloud, etc.).

---

Update this file as you make progress on each task. 