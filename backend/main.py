from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from auth.routes import router as auth_router
from assessment.routes import router as assessment_router
from database.session import SessionLocal, engine, Base
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Enhanced CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:3000",  # Add your React port
        "http://127.0.0.1",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.on_event("startup")
async def startup_event():
    try:
        # Create all database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
        
        # Optional: Add initial test data
        db = SessionLocal()
        try:
            from auth.models import User
            if not db.query(User).first():
                test_user = User(
                    email="admin@example.com", 
                    hashed_password="placeholder_hashed_password"
                )
                db.add(test_user)
                db.commit()
                logger.info("Initial test user created")
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

app.include_router(auth_router, prefix="/auth")
app.include_router(assessment_router, prefix="/assessment")

@app.get("/")
def health_check():
    return {"status": "AI Agent is running"}