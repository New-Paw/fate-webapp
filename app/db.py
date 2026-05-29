from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Create the database engine "engine".
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# Create Session Factory SessionLocal.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create the base class for the ORM model.
Base = declarative_base()

# Database dependency function: get_db().
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()