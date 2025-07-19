from fastapi import APIRouter, HTTPException, Depends, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from datetime import timedelta
from auth.models import User
from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from database.session import get_db
from sqlalchemy.orm import Session
from pydantic import BaseModel

router = APIRouter()

class UserCreate(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_email: str

@router.options("/register")
async def options_register():
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "http://localhost",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Credentials": "true"
        }
    )

@router.post("/register")
async def register(user: UserCreate, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    db_user = User(
        email=user.email,
        hashed_password=hash_password(user.password)
    )
    db.add(db_user)
    db.commit()
    
    response.headers["Access-Control-Allow-Origin"] = "http://localhost"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return {"message": "User created successfully"}

@router.post("/login", response_model=Token)
async def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=access_token_expires
    )
    
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=1800,
        secure=False,
        samesite='lax'
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_email": user.email
    }