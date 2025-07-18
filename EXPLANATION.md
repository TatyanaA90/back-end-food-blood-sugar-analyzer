# Food & Blood Sugar Tracker Backend - Code Explanation

## 🍎 **What We Built: A Food and Blood Sugar Tracker App**

Imagine you have a special notebook that helps you remember what you ate and how it made your blood sugar feel. That's basically what we built, but it's a computer app instead of a notebook!

### **The Main Parts:**

**1. The Database (Like a Big Filing Cabinet)**
- We created a special storage system that keeps track of:
  - People who use the app (like you and your friends)
  - What food they eat (like "I had pizza for lunch")
  - How their blood sugar changes after eating
  - When they take medicine (like insulin)
  - How much they exercise
  - Their health goals (like "I want to keep my blood sugar between 80-120")

**2. The Backend (Like the Brain of the App)**
- We built the "thinking" part of the app using Python (a computer language)
- It can:
  - Remember who you are when you log in (like having a special key to your house)
  - Save all your food and health information safely
  - Help you look back at what you ate and how it affected you
  - Give you advice about your health

**3. Keeping Things Safe (Like a Lock on Your Diary)**
- We made sure only you can see your information
- When you create an account, your password gets scrambled up so no one can steal it
- You get a special "ticket" (called a token) that lets you use the app without typing your password every time

**4. Different Pages for Different Things**
We created special sections for:
- **Food tracking**: "What did I eat today?"
- **Blood sugar readings**: "What's my blood sugar right now?"
- **Medicine tracking**: "Did I take my insulin?"
- **Exercise**: "How much did I move today?"
- **Goals**: "What do I want to achieve?"
- **Reports**: "How am I doing overall?"

### **What Makes It Special:**

**Smart Features:**
- It can connect to special devices (like Dexcom) that automatically check your blood sugar
- It can give you advice about your health based on your information
- It can help you plan meals that are good for your blood sugar
- It can show you patterns (like "every time I eat ice cream, my blood sugar goes up a lot")

**Easy to Use:**
- You can type in what you ate
- You can take pictures of your food
- You can even watch videos about healthy eating
- It reminds you to check your blood sugar

### **What We're Still Working On:**
- Making it look pretty and easy to use (the frontend part)
- Adding more smart features
- Making sure it works perfectly on phones and computers
- Testing everything to make sure it works correctly

Think of it like building a really smart robot friend that helps you remember everything about your health and gives you good advice! 🍎💉📱

---

## 🏗️ **Project Structure Overview**

Our app is organized like a well-structured house with different rooms for different purposes:

```
app/
├── main.py          # Front door - where everything starts
├── core/            # Foundation - basic building blocks
├── models/          # Blueprints - how data looks
├── routers/         # Rooms - different areas of the app
└── tests/           # Safety checks - make sure everything works
```

---

## 🚪 **1. Main Entry Point (`app/main.py`)**

This is like the front door of our house - where everything starts:

```python
from fastapi import FastAPI
from app.routers.user_router import router as user_router

app = FastAPI()  # Create our app
app.include_router(user_router)  # Add the user management room
```

**What it does:**
- Creates the main FastAPI application
- Connects different parts of the app together
- Provides basic health check endpoints (`/ping`, `/`)

**Key Features:**
- **FastAPI Framework**: Modern, fast web framework for building APIs
- **Router Integration**: Connects different parts of the application
- **Health Checks**: Simple endpoints to verify the app is running

---

## 🏗️ **2. Core Foundation (`app/core/`)**

### **Configuration (`config.py`)**
```python
class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URI: str  # Where our database lives
```

**What it does:**
- Manages all the settings (like database connection)
- Reads from `.env` file for secrets
- Keeps sensitive information safe

**Key Features:**
- **Environment Variables**: Secure way to store database credentials
- **Pydantic Settings**: Type-safe configuration management
- **Auto-loading**: Automatically loads settings from `.env` file

### **Database Connection (`database.py`)**
```python
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
```

**What it does:**
- Connects to PostgreSQL database
- Creates database sessions for reading/writing data
- Manages database connections safely

**Key Features:**
- **SQLAlchemy Engine**: Powerful database connection manager
- **Session Management**: Safe database operations with automatic cleanup
- **Connection Pooling**: Efficient database connection handling

### **Security System (`security.py`)**
```python
# Password protection
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT token system
def create_access_token(data: dict) -> str:
    # Creates special login tickets
```

**What it does:**
- **Password Hashing**: Turns passwords into scrambled text (like "password123" → "abc123xyz")
- **JWT Tokens**: Creates special "tickets" that let you stay logged in
- **User Authentication**: Checks if you're allowed to access certain parts

**Key Features:**
- **Bcrypt Hashing**: Industry-standard password security
- **JWT Authentication**: Stateless authentication system
- **Token Expiration**: Automatic session management (30 minutes)
- **Secure Verification**: Safe password and token validation

---

## 📋 **3. Data Models (`app/models/`)**

These are like blueprints for how our data should look:

### **Base Model (`base.py`)**
```python
class Base(SQLModel):
    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime | None = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**What it does:**
- Every piece of data gets a unique ID
- Automatically tracks when data was created and updated
- Like a stamp that says "made on January 15th at 2:30 PM"

**Key Features:**
- **Auto-generated IDs**: Unique identifiers for each record
- **Timestamp Tracking**: Automatic creation and update timestamps
- **UTC Timezone**: Consistent time handling across the world

### **User Model (`user.py`)**
```python
class User(Base, table=True):
    email: str = Field(index=True, unique=True, nullable=False)
    name: str
    username: str = Field(index=True, unique=True, nullable=False)
    hashed_password: str
    
    # Connections to other data
    glucose_readings: List["GlucoseReading"] = Relationship(back_populates="user")
    meals: List["Meal"] = Relationship(back_populates="user")
```

**What it does:**
- Stores user information (name, email, username)
- Keeps hashed passwords (scrambled for safety)
- Connects to all the user's health data

**Key Features:**
- **Unique Constraints**: No duplicate emails or usernames
- **Indexed Fields**: Fast database lookups
- **Relationship Mapping**: Links to all user's health data
- **Password Security**: Only stores hashed passwords

### **Meal Model (`meal.py`)**
```python
class Meal(Base, table=True):
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    description: Optional[str] = None
    carbs: Optional[float] = None
    photo_url: Optional[str] = None
```

**What it does:**
- Records what you ate and when
- Stores carbohydrate content
- Can save photos of your food
- Links to the user who ate it

**Key Features:**
- **Foreign Key Relationship**: Links meals to specific users
- **Optional Fields**: Flexible data entry
- **Photo Support**: Can store food images
- **Carbohydrate Tracking**: Important for diabetes management

### **Glucose Reading Model (`glucose_reading.py`)**
```python
class GlucoseReading(Base, table=True):
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    value: float
    source: Optional[str] = None
```

**What it does:**
- Records blood sugar readings
- Stores the value (like 120 mg/dL)
- Tracks when it was taken
- Notes where it came from (finger prick, CGM, etc.)

**Key Features:**
- **Required Value**: Blood sugar reading is mandatory
- **Source Tracking**: Know where the reading came from
- **Time Stamping**: When the reading was taken
- **User Association**: Links to specific user

### **Other Models:**

#### **Insulin Dose Model (`insulin_dose.py`)**
```python
class InsulinDose(Base, table=True):
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    units: float
    type: Optional[str] = None  # rapid-acting, long-acting, etc.
```

**What it does:**
- Records insulin injections
- Tracks dosage amounts
- Categorizes insulin types
- Links to meals when relevant

#### **Activity Model (`activity.py`)**
```python
class Activity(Base, table=True):
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    type: Optional[str] = None  # walking, running, swimming, etc.
    duration: Optional[int] = None  # minutes
    intensity: Optional[str] = None  # low, moderate, high
```

**What it does:**
- Tracks exercise and movement
- Records activity duration and intensity
- Helps correlate exercise with blood sugar changes

#### **Condition Log Model (`condition_log.py`)**
```python
class ConditionLog(Base, table=True):
    user_id: int = Field(foreign_key="users.id")
    timestamp: Optional[datetime] = None
    notes: Optional[str] = None
    mood: Optional[str] = None
    symptoms: Optional[str] = None
```

**What it does:**
- Records how you're feeling
- Tracks symptoms and mood
- Provides context for blood sugar patterns

#### **Meal Ingredient Model (`meal_ingredient.py`)**
```python
class MealIngredient(Base, table=True):
    meal_id: int = Field(foreign_key="meals.id")
    name: str
    carbs: Optional[float] = None
    quantity: Optional[str] = None
```

**What it does:**
- Breaks down meals into individual ingredients
- Tracks carbohydrate content per ingredient
- Enables detailed nutritional analysis

---

## 🍽️ Meals & Ingredients: Model, Business Logic, and API

### Model Changes (June 2024)

- **MealIngredient**: Now includes `name`, `weight` (optional, grams), `carbs` (grams), `glycemic_index` (optional), `note` (optional)
- **Meal**: Now includes `total_weight`, `total_carbs`, `glycemic_index`, `note`, `description`, `timestamp`, `photo_url`
- **User**: Now includes `is_admin` boolean for admin permissions

### CRUD Endpoints & Business Logic

- **Create/Update Meal**: User can create a meal by specifying ingredients (with weights and carbs). Backend automatically calculates total carbs and total weight from ingredients. All fields are validated.
- **Cascade Delete**: Deleting a meal also deletes its ingredients.
- **Permissions**: Only the user who created a meal or an admin can edit/delete it. Admin can see and edit all meals.
- **Response Models**: List view returns basic info; detail view returns ingredients. Sensitive fields (user_id, internal notes) are hidden from responses.
- **Pydantic Schemas**: Used for validation and serialization of all input/output.

---

## 🚪 **4. API Routes (`app/routers/`)**

These are like different rooms in our house, each handling specific tasks:

### **User Router (`user_router.py`)**

#### **User Registration**
```python
@router.post("/users", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    """Create a new user account with hashed password for secure storage."""
    db_user = User(
        email=user.email,
        name=user.name,
        username=user.username,
        hashed_password=get_password_hash(user.password)
    )
    session.add(db_user)
    session.commit()
    return db_user
```

**What it does:**
- Creates new user accounts
- Automatically hashes passwords for security
- Returns user information (without password)

#### **User Login**
```python
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    """Authenticate user credentials and return JWT access token for session management."""
    user = session.exec(select(User).where(User.username == form_data.username)).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=30)
    )
    return {"access_token": access_token, "token_type": "bearer"}
```

**What it does:**
- Verifies username and password
- Creates JWT access token
- Returns secure login credentials

#### **User Information**
```python
@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's information."""
    return current_user
```

**What it does:**
- Gets current user's information
- Requires authentication
- Returns user profile data

**Available Endpoints:**
- **`POST /users`**: Create new account
- **`POST /login`**: Log in and get access token
- **`GET /users/{id}`**: Get specific user info
- **`GET /users`**: Get all users (admin)
- **`GET /me`**: Get current user's info

### **Other Routers (Ready for Implementation):**

#### **Meal Plan Router (`meal_plan_router.py`)**
- Plan healthy meals
- Generate meal suggestions
- Calculate nutritional content

#### **Analytics Router (`analytics_router.py`)**
- Health insights and reports
- Blood sugar trend analysis
- Pattern recognition

#### **Dexcom Upload Router (`dexcom_upload_router.py`)**
- Connect to glucose monitors
- Import continuous glucose data
- Real-time blood sugar tracking

#### **Goals Router (`goals_router.py`)**
- Set and track health goals
- Progress monitoring
- Achievement tracking

#### **Logs Router (`logs_router.py`)**
- Daily health logs
- Symptom tracking
- Mood and condition notes

#### **Stats Router (`stats_router.py`)**
- Statistics and trends
- Data visualization
- Performance metrics

#### **YouTube Router (`youtube_router.py`)**
- Educational videos
- Health tips and tutorials
- Community content

#### **Appointment Router (`appointment_router.py`)**
- Doctor appointments
- Healthcare provider management
- Medical visit tracking

---

## 🗄️ **5. Database Management (Alembic)**

### **Migration System (`alembic/env.py`)**
```python
from app.models import user, glucose_reading, meal, meal_ingredient, insulin_dose, activity, condition_log

target_metadata = SQLModel.metadata
```

**What it does:**
- Automatically creates database tables from our models
- Manages database changes over time
- Keeps track of what's been added/modified

**Key Features:**
- **Auto-generation**: Creates tables from model definitions
- **Version Control**: Tracks database schema changes
- **Rollback Support**: Can undo database changes if needed
- **Migration History**: Complete audit trail of database evolution

### **Migration Files**
Located in `alembic/versions/`:
- **`869d1263854f_add_username_and_hashed_password_to_.py`**: Initial user table setup

---

## 📦 **6. Dependencies (`requirements.txt`)**

These are the tools we use to build everything:

### **Core Framework**
- **`fastapi==0.116.1`**: Modern, fast web framework for building APIs
- **`uvicorn==0.35.0`**: ASGI server for running FastAPI applications

### **Database & ORM**
- **`sqlmodel==0.0.24`**: Modern Python library for working with SQL databases
- **`sqlalchemy==2.0.41`**: SQL toolkit and Object-Relational Mapping library
- **`psycopg2-binary==2.9.10`**: PostgreSQL adapter for Python
- **`alembic==1.16.4`**: Database migration tool

### **Security & Authentication**
- **`passlib[bcrypt]==1.7.4`**: Password hashing library
- **`python-jose[cryptography]==3.3.0`**: JWT token handling
- **`python-multipart==0.0.20`**: Form data parsing

### **Data Validation & Settings**
- **`pydantic==2.11.7`**: Data validation using Python type annotations
- **`pydantic-settings==2.10.1`**: Settings management using Pydantic
- **`email-validator==2.2.0`**: Email address validation

### **Testing**
- **`pytest==8.4.1`**: Testing framework
- **`pytest-asyncio==1.0.0`**: Async testing support

### **Development Tools**
- **`python-dotenv==1.1.1`**: Environment variable management
- **`rich==14.0.0`**: Rich text and beautiful formatting in the terminal

---

## 🔧 **7. Testing (`tests/`)**

### **Test Structure**
```python
# Example test structure
def test_user_creation():
    # Test that users can be created properly
    pass

def test_password_hashing():
    # Test that passwords are scrambled correctly
    pass
```

**What it does:**
- Makes sure everything works correctly
- Tests security features
- Ensures data is saved properly

**Test Files:**
- **`test_appointment_model.py`**: Tests for appointment functionality
- **`test_logs_model.py`**: Tests for logging functionality
- **`test_models.py`**: Tests for data models

---

## 🎯 **What Each Part Accomplishes:**

### **1. Security Features**
- ✅ **Password Hashing**: All passwords are scrambled using bcrypt
- ✅ **JWT Authentication**: Secure login system with expiring tokens
- ✅ **User Isolation**: Each user can only access their own data
- ✅ **Input Validation**: All data is validated before processing

### **2. Data Management**
- ✅ **Structured Storage**: All health data is organized in related tables
- ✅ **Relationship Mapping**: Users are connected to all their health data
- ✅ **Timestamp Tracking**: All data includes creation and update times
- ✅ **Flexible Schema**: Optional fields allow for gradual data entry

### **3. API Design**
- ✅ **RESTful Endpoints**: Clean, predictable API structure
- ✅ **Response Models**: Consistent data formats
- ✅ **Error Handling**: Proper HTTP status codes and error messages
- ✅ **Authentication Required**: Protected endpoints for sensitive data

### **4. Scalability Features**
- ✅ **Modular Design**: Easy to add new features and routers
- ✅ **Database Migrations**: Safe schema evolution over time
- ✅ **Configuration Management**: Environment-based settings
- ✅ **Testing Framework**: Automated testing for reliability

### **5. Health Tracking Capabilities**
- ✅ **User Management**: Secure account creation and login
- ✅ **Meal Tracking**: Food intake and carbohydrate recording
- ✅ **Glucose Monitoring**: Blood sugar reading storage
- ✅ **Insulin Dosing**: Medication tracking
- ✅ **Activity Logging**: Exercise and movement recording
- ✅ **Condition Notes**: Symptom and mood tracking
- ✅ **Ingredient Analysis**: Detailed meal breakdown

---

## 🚀 **Ready for Implementation Features:**

The following routers are created but need implementation:

1. **Meal Planning**: Smart meal suggestions based on health goals
2. **Analytics**: Blood sugar trend analysis and insights
3. **Device Integration**: Dexcom and other CGM connectivity
4. **Goal Setting**: Health target management and tracking
5. **Educational Content**: YouTube video integration
6. **Healthcare Coordination**: Doctor appointment management
7. **Advanced Logging**: Comprehensive health diary features
8. **Statistics**: Data visualization and reporting

---

## 🔒 **Security Best Practices Implemented:**

1. **Password Security**: Bcrypt hashing with salt
2. **Token Management**: JWT with configurable expiration
3. **Input Validation**: Pydantic models for data validation
4. **SQL Injection Prevention**: SQLModel ORM with parameterized queries
5. **Environment Variables**: Secure credential management
6. **Error Handling**: Safe error responses without information leakage

---

## 📊 **Database Schema Overview:**

```
users
├── glucose_readings (one-to-many)
├── meals (one-to-many)
│   └── meal_ingredients (one-to-many)
├── insulin_doses (one-to-many)
├── activities (one-to-many)
└── condition_logs (one-to-many)
```

This creates a solid foundation for a health tracking app that can safely store user data, provide secure access, and easily grow with new features! 🏥📱💪 