from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base,scoped_session
import os



DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:krokodil@localhost:5432/editor_db")

# Create engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True shows SQL queries

# Create a configured "Session" class
SessionLocal = scoped_session(sessionmaker(bind=engine))
# Base class for models
Base = declarative_base()
