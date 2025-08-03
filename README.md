# Food & Blood Sugar Analyzer - Backend API

A comprehensive FastAPI backend for diabetes management and blood sugar tracking, providing robust data management and analytics for the Food & Blood Sugar Analyzer application.

## 🏥 About

This backend API serves the Food & Blood Sugar Analyzer frontend application, providing secure data storage, comprehensive analytics, and health insights for diabetes management. It handles glucose readings, meals, activities, insulin doses, and generates detailed analytics and recommendations.

## 🚀 Tech Stack

- **Framework**: FastAPI (Python)
- **Database ORM**: SQLModel (SQLAlchemy v2)
- **Database**: PostgreSQL
- **Authentication**: JWT tokens with OAuth2
- **Migrations**: Alembic
- **Validation**: Pydantic v2
- **Testing**: pytest with TestClient
- **Deployment**: Render (Web Service)

## ✨ Features

### Core Data Management
- 🩸 **Glucose Readings**: Track blood sugar levels with unit support (mg/dL, mmol/L)
- 🍽️ **Meals**: Comprehensive meal tracking with ingredients and nutrition calculations
- 🏃 **Activities**: Exercise logging with MET-based calorie calculations
- 💉 **Insulin Doses**: Insulin tracking with type and unit management
- 📋 **Condition Logs**: Health condition and symptom tracking
- 🎯 **Goals**: Health goal setting and progress tracking

### Analytics & Insights
- 📊 **Glucose Summary**: Statistical analysis with period grouping
- 📈 **Glucose Trends**: Time-series data for visualization
- 🎯 **Time in Range**: Target range analysis
- 📉 **Glucose Variability**: Standard deviation, CV, and GMI calculations
- 🚨 **Glucose Events**: Hypo/hyperglycemia event detection
- 🍽️ **Meal Impact**: Before/after meal glucose analysis
- 🏃 **Activity Impact**: Exercise effect on glucose levels
- 💉 **Insulin Correlation**: Insulin-glucose relationship analysis
- 🤖 **AI Recommendations**: Actionable insights and alerts

### File Upload
- 📤 **CGM CSV Upload**: Continuous glucose monitor data import
- 📊 **Data Processing**: Automatic parsing and validation
- 🔄 **Format Support**: Multiple CGM device formats

## 🛠️ Development

### Prerequisites
- Python 3.11+
- PostgreSQL
- pip or poetry

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/back-end-food-blood-sugar-analyzer.git

# Navigate to project directory
cd back-end-food-blood-sugar-analyzer

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run database migrations
alembic upgrade head

# Start development server
uvicorn app.main:app --reload
```

### Environment Variables

```env
DATABASE_URL=postgresql://user:password@localhost/dbname
SQLALCHEMY_TEST_DATABASE_URI=postgresql://user:password@localhost/test_dbname
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 🌐 Production Deployment

- **API URL**: https://back-end-food-blood-sugar-analyzer.onrender.com
- **Database**: Render PostgreSQL
- **Status**: Live and operational
- **Documentation**: Available at `/docs` (Swagger UI)

## 📡 API Endpoints

### Authentication
- `POST /users` - User registration
- `POST /login` - User login (OAuth2 form)
- `GET /me` - Get current user
- `GET /users/{user_id}` - Get user by ID
- `GET /users` - Get all users (admin)

### Core Data
- `GET/POST/PUT/DELETE /glucose-readings` - Glucose readings CRUD
- `GET/POST/PUT/DELETE /meals` - Meals CRUD  
- `GET/POST/PUT/DELETE /activities` - Activities CRUD
- `GET/POST/PUT/DELETE /insulin-doses` - Insulin doses CRUD
- `GET/POST/PUT/DELETE /condition-logs` - Condition logs CRUD

### Analytics
- `GET /analytics/glucose-summary` - Summary statistics
- `GET /analytics/glucose-trend` - Trend data for charts
- `GET /analytics/agp-overlay` - AGP overlay data
- `GET /analytics/time-in-range` - Time in range analysis
- `GET /analytics/glucose-variability` - Variability metrics
- `GET /analytics/glucose-events` - Event timeline
- `GET /analytics/meal-impact` - Meal impact analysis
- `GET /analytics/activity-impact` - Activity impact analysis
- `GET /analytics/insulin-glucose-correlation` - Correlation analysis
- `GET /analytics/recommendations` - AI recommendations

### Visualization
- `GET /visualization/dashboard-overview` - Dashboard data
- `GET /visualization/glucose-timeline` - Timeline with events
- `GET /visualization/data-quality-metrics` - Data quality assessment

### File Upload
- `POST /upload/cgm-csv` - CGM CSV file upload

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_users.py

# Run with verbose output
pytest -v
```

### Test Coverage
- ✅ **38 tests** passing successfully
- ✅ **All endpoints** covered
- ✅ **Authentication** fully tested
- ✅ **CRUD operations** validated
- ✅ **Analytics** endpoints verified
- ✅ **Error handling** tested

## 📁 Project Structure

```
app/
├── main.py                 # FastAPI application
├── database.py            # Database configuration
├── models/                 # SQLModel models
│   ├── user.py            # User model
│   ├── glucose_reading.py # Glucose reading model
│   ├── meal.py            # Meal and ingredient models
│   ├── activity.py        # Activity model
│   └── ...                # Other models
├── routers/               # API route handlers
│   ├── user_router.py     # User authentication
│   ├── glucose_router.py  # Glucose readings
│   ├── analytics_router.py # Analytics endpoints
│   └── ...                # Other routers
├── services/              # Business logic
│   ├── auth_service.py    # Authentication logic
│   ├── analytics_service.py # Analytics calculations
│   └── ...                # Other services
└── utils/                 # Utility functions
    ├── security.py        # Password hashing, JWT
    ├── calculations.py    # Health calculations
    └── ...                # Other utilities
```

## 🔧 Technical Achievements

- **Modern Python**: Pydantic v2, async/await, type hints
- **Clean Architecture**: Separation of concerns, dependency injection
- **Comprehensive Testing**: 100% endpoint coverage
- **Data Validation**: Robust input validation and sanitization
- **Security**: JWT authentication, password hashing, SQL injection protection
- **Performance**: Optimized queries, connection pooling
- **Documentation**: Auto-generated API docs with Swagger UI

## 🔗 Frontend Integration

- **Frontend Repository**: [Food & Blood Sugar Analyzer Frontend](https://github.com/TatyanaA90/front-end-food-blood-sugar-analyzer.git)
- **Frontend URL**: https://food-blood-sugar-analyzer-frontend.onrender.com
- **API Integration**: Seamless connection via Axios HTTP client
- **Authentication**: JWT token-based authentication flow
- **Real-time Data**: Optimistic updates with React Query

---

*Built with ❤️ for better diabetes management*
