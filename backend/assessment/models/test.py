from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime
from database.session import Base
from datetime import datetime

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    questions = Column(JSON)
    answers = Column(JSON, nullable=True)
    score = Column(Integer, nullable=True)
    rule_based_strength = Column(String, nullable=True)
    ml_based_strength = Column(String, nullable=True)
    feedback = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)