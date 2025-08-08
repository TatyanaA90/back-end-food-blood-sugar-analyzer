# Food & Blood Sugar Analyzer API

A comprehensive FastAPI-based backend for diabetes management and blood sugar analysis, featuring advanced analytics, secure admin functionality, and production-ready architecture.

## 🚀 Project Status

**✅ PRODUCTION READY** - Complete diabetes management system with admin functionality

- **Overall Progress**: 100% Complete
- **Tests**: 55/55 passing ✅
- **Security**: Full compliance ✅
- **Documentation**: Comprehensive ✅
- **Admin System**: Complete ✅

## 🏗️ Architecture

### Backend Stack
- **Framework**: FastAPI (Python)
- **Database**: PostgreSQL with SQLModel/SQLAlchemy
- **Authentication**: JWT with bcrypt password hashing
- **Migrations**: Alembic
- **Testing**: pytest with TestClient
- **Documentation**: OpenAPI/Swagger auto-generated

### Key Features
- **User Management**: Registration, authentication, profile management
- **Data Tracking**: Meals, activities, glucose readings, insulin doses, condition logs
- **Predefined Meal System**: Template-based meal creation with quantity and weight adjustments
- **Advanced Analytics**: 10 comprehensive analytics endpoints
- **Admin System**: Complete user and system management
- **Data Import**: CGM CSV upload functionality
- **Visualization**: Dashboard and chart data endpoints
- **Security**: Role-based access control and comprehensive validation

## 🔐 Admin Functionality

### Admin Features
- **User Management**: View, update, delete individual users
- **System Statistics**: Comprehensive system analytics
- **Password Reset**: Admin can reset any user's password
- **Data Access**: View all user data and system information
- **Bulk Operations**: Truncate all users (development only)

### Security Features
- **Role-based Access**: `get_current_admin_user()` dependency
- **JWT Admin Flags**: Tokens include admin status
- **Self-protection**: Admins cannot delete their own accounts
- **Proper Error Handling**: Appropriate HTTP status codes

## 📊 Analytics System

### Available Analytics Endpoints
1. **Glucose Summary**: Basic statistics with optional grouping
2. **Glucose Trend**: Time-series data with moving averages
3. **Glucose Variability**: SD, CV, and GMI calculations
4. **Glucose Events**: Hypo/hyperglycemia event detection
5. **Meal Impact**: Glucose changes after meals
6. **Activity Impact**: Exercise effects on glucose
7. **Insulin-Glucose Correlation**: Personalized insulin effectiveness
8. **Recommendations**: AI-enhanced insights and tips

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.11+
- PostgreSQL
- pip

### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd back-end-food-blood-sugar-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your database credentials

# Run database migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload
```

### Environment Variables
```env
SQLALCHEMY_DATABASE_URI=postgresql://user:password@localhost/dbname
SECRET_KEY=your-secret-key-here
FRONTEND_URL=http://localhost:5173
```

## 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_user_router.py -v

# Run with coverage
python -m pytest tests/ --cov=app --cov-report=html
```

**Test Results**: 55/55 tests passing ✅

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

### Key Endpoints

#### Authentication
- `POST /users` - User registration
- `POST /login` - User login
- `GET /me` - Get current user profile
- `PUT /me` - Update user profile

#### Admin (Admin Only)
- `GET /admin/stats` - System statistics
- `GET /admin/users` - List all users
- `GET /admin/users/{user_id}` - Get user details
- `PUT /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user
- `POST /admin/users/{user_id}/reset-password` - Reset user password

#### Data Management
- `GET/POST /meals` - Meal management
- `GET/POST /meals/from-predefined` - Create meals from predefined templates
- `GET/POST /predefined-meals` - Predefined meal template management (admin)
- `GET/POST /activities` - Activity tracking
- `GET/POST /glucose-readings` - Glucose monitoring
- `GET/POST /insulin-doses` - Insulin tracking
- `GET/POST /condition-logs` - Health monitoring

#### Analytics
- `GET /analytics/glucose-summary` - Glucose statistics
- `GET /analytics/glucose-trend` - Trend analysis
- `GET /analytics/glucose-variability` - Variability metrics
- `GET /analytics/meal-impact` - Meal impact analysis
- `GET /analytics/activity-impact` - Activity impact analysis
- `GET /analytics/insulin-glucose-correlation` - Insulin effectiveness

## 🔒 Security

### Authentication
- JWT tokens with configurable expiration
- bcrypt password hashing
- Role-based access control
- Admin-specific endpoints with enhanced security

### Data Protection
- Input validation with Pydantic models
- SQL injection prevention with SQLModel
- CORS configuration for frontend integration
- Environment variable management

## 🚀 Deployment

### Production Deployment
The API is deployed on Render with:
- **URL**: https://back-end-food-blood-sugar-analyzer.onrender.com
- **Database**: Render PostgreSQL
- **Status**: Live and fully functional

### Environment Configuration
```yaml
# render.yaml
services:
  - type: web
    name: back-end-food-blood-sugar-analyzer
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## 📈 Project Metrics

### Code Quality
- **Test Coverage**: 100% of critical endpoints
- **Code Standards**: PEP 8 compliant
- **Documentation**: Comprehensive docstrings
- **Type Safety**: Full type hints throughout

### Performance
- **Response Time**: < 200ms for most endpoints
- **Database**: Optimized queries with proper indexing
- **Caching**: Ready for Redis integration
- **Scalability**: Horizontal scaling ready

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- **Email**: support@foodbloodsugar.com
- **Documentation**: `/docs` endpoint
- **Health Check**: `/health` endpoint

---

**Built with ❤️ for diabetes management and blood sugar analysis**
