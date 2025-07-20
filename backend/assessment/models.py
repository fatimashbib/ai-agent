from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from database.session import Base
from sqlalchemy.sql import func

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    questions = Column(JSON)
    answers = Column(JSON)
    score = Column(Integer)
    rule_based_strength = Column(String, nullable=True)  # e.g., "Strong", "Moderate"
    ml_based_strength = Column(String, nullable=True)    # optional, if you want labels from ML
    feedback = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # Add this line
    completed_at = Column(DateTime(timezone=True), nullable=True)  # Add completion timestamp to measure duration
