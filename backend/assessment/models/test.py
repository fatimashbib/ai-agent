from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from database.session import Base

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    questions = Column(JSON)
    answers = Column(JSON, nullable=True)
    rule_based_score = Column(Integer, nullable=True)
    ml_based_score = Column(Integer, nullable=True)
    feedback = Column(String, nullable=True)