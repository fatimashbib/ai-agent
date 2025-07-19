from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import requests
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from .scoring import Scorer
from .prompts import CRITICAL_THINKING_PROMPT
from database.session import get_db
from auth.security import get_current_user
import json
import os
from assessment.models.test import Test

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
scorer = Scorer()

class DeepSeekAPI:
    def __init__(self, api_key: str):
        self.base_url = "https://api.deepseek.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    def generate(self, model: str, messages: list, response_format: Optional[dict] = None) -> Dict:
        payload = {
            "model": model,
            "messages": messages,
            "temperature": 0.7
        }
        if response_format:
            payload["response_format"] = response_format
            
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers=self.headers,
            json=payload
        )
        response.raise_for_status()
        return response.json()

# Initialize DeepSeek client with API key from environment variables
ds = DeepSeekAPI(api_key=os.getenv("DEEPSEEK_API_KEY", "sk-c2f1f20e654441eb8ba47f51ce683c40"))

class TestResponse(BaseModel):
    questions: List[Dict]
    test_id: int

class EvaluationRequest(BaseModel):
    answers: Dict[str, str]
    test_id: int

@router.post("/generate-test", response_model=TestResponse)
async def generate_test(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    
    try:
        # Call DeepSeek API
        response = ds.generate(
            model="deepseek-chat",
            messages=[{"role": "user", "content": CRITICAL_THINKING_PROMPT}],
            response_format={"type": "json_object"}
        )
        
        # Parse the response
        content = json.loads(response["choices"][0]["message"]["content"])
        questions = content["questions"]
        
        # Store test in database
        test = Test(user_id=user.id, questions=questions)
        db.add(test)
        db.commit()
        
        return {"questions": questions, "test_id": test.id}
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=502,
            detail=f"DeepSeek API request failed: {str(e)}"
        )
    except (KeyError, json.JSONDecodeError) as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to parse DeepSeek response: {str(e)}"
        )

@router.post("/evaluate-test")
async def evaluate_test(
    request: EvaluationRequest,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    user = get_current_user(token, db)
    test = db.query(Test).filter(Test.id == request.test_id).first()
    
    if not test or test.user_id != user.id:
        raise HTTPException(status_code=404, detail="Test not found")
    
    try:
        # Calculate scores
        rule_score = scorer.rule_based_score(test.questions, request.answers)
        ml_score = scorer.ml_based_score(test.questions, request.answers)
        
        # Update test record
        test.answers = request.answers
        test.rule_based_score = rule_score
        test.ml_based_score = ml_score
        test.feedback = generate_feedback(rule_score, ml_score)
        db.commit()
        
        return {
            "rule_based": {"score": rule_score, "max": 100},
            "ml_based": {"score": ml_score, "max": 10},
            "feedback": test.feedback
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Evaluation failed: {str(e)}"
        )

def generate_feedback(rule_score: float, ml_score: float) -> str:
    if rule_score > 80 and ml_score > 8:
        return "Excellent critical thinking skills!"
    elif rule_score > 60:
        return "Good analytical abilities with room for improvement"
    else:
        return "Keep practicing - focus on evaluating arguments systematically"