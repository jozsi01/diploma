from sqlalchemy import create_engine, URL
from sqlalchemy.orm import sessionmaker, declarative_base,scoped_session


db_url = URL.create(
    drivername="postgresql",
    username="postgres",
    password="krokodil",
    host="localhost",
    port=5432,
    database="editor_db"
)

DATABASE_URL = "postgresql://postgres:krokodil@localhost:5432/editor_db"

# Create engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True shows SQL queries

# Create a configured "Session" class
SessionLocal = scoped_session(sessionmaker(bind=engine))
# Base class for models
Base = declarative_base()
