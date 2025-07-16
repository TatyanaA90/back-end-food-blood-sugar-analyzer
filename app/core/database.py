from sqlmodel import create_engine, Session
from .config import settings

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
