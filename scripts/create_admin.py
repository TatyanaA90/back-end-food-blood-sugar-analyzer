from sqlmodel import Session, select
from app.core.database import get_session
from app.models.user import User
from app.core.security import get_password_hash

def create_admin_user(
    email: str,
    username: str,
    name: str,
    password: str,
    session: Session
) -> User:
    # Check if user already exists
    existing_user = session.exec(
        select(User).where(
            (User.email == email) | (User.username == username)
        )
    ).first()
    
    if existing_user:
        print(f"User with email {email} or username {username} already exists")
        return existing_user
    
    # Create new admin user
    admin_user = User(
        email=email,
        username=username,
        name=name,
        hashed_password=get_password_hash(password),
        is_admin=True
    )
    
    session.add(admin_user)
    session.commit()
    session.refresh(admin_user)
    
    print(f"Created admin user: {username}")
    return admin_user

if __name__ == "__main__":
    # Get database session
    session = next(get_session())
    
    # Create admin user
    admin = create_admin_user(
        email="admin@example.com",
        username="admin",
        name="Admin User",
        password="Admin123!",  # Change this!
        session=session
    )