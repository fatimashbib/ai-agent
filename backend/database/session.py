from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Create db directory if it doesn't exist
os.makedirs('/app/db', exist_ok=True)

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:////app/db/ai-agent.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    pool_pre_ping=True
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Add this function for dependency injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()