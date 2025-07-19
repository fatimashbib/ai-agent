from sqlalchemy import Column, Integer, String
from database.session import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True)
    hashed_password = Column(String(100))