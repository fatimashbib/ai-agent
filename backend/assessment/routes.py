import regex as re
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List,Any
from sqlalchemy import desc
import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .scoring import Scorer, StrengthEvaluator
from .prompts import CRITICAL_THINKING_PROMPT
from database.session import get_db
from auth.security import get_current_user
from assessment.models.test import Test
from dotenv import load_dotenv



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter(
    tags=["assessment"],
    responses={404: {"description": "Not found"}}
)

load_dotenv()
strength_evaluator = StrengthEvaluator()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
scorer = Scorer()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class Question(BaseModel):
    id: int
    text: str
    options: List[str]
    correct_index: int
    explanation: Optional[str] = None

class TestResponse(BaseModel):
    questions: List[Question]
    test_id: int

class StructuredFeedback(BaseModel):
    overview: str
    strengths: List[str]
    improvements: List[str]

class ScoreDetails(BaseModel):
    value: float
    max: float = 100.0
    percentage: float
    rule_based_strength: str  # "Strong", "Moderate", "Weak"
    ml_based_strength: str    # "Strong", "Moderate", "Weak"

class EvaluationResponse(BaseModel):
    score: ScoreDetails
    feedback: StructuredFeedback
    detailed_feedback: Optional[Dict[int, str]] = None

class EvaluationRequest(BaseModel):
    test_id: int
    answers: Dict[str, int]

class TestHistoryItem(BaseModel):
    id: int
    score: float
    rule_based_strength: str
    ml_based_strength: str
    created_at: datetime
    completed_at: datetime
    feedback: Optional[Dict[str, Any]] = None

class TestHistoryResponse(BaseModel):
    tests: List[TestHistoryItem]

def extract_json_from_string(text: str) -> Optional[str]:
    json_match = re.search(r"\{(?:[^{}]|(?R))*\}", text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None

@router.get("/test-history", response_model=TestHistoryResponse)
async def get_test_history(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from auth.models import User
    user = db.query(User).filter(User.email == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    tests = db.query(Test).filter(
        Test.user_id == user.id,
        Test.score.isnot(None)
    ).order_by(desc(Test.created_at)).all()

    return TestHistoryResponse(
        tests=[
            TestHistoryItem(
                id=test.id,
                score=test.score,
                rule_based_strength=test.rule_based_strength,
                ml_based_strength=test.ml_based_strength,
                created_at=test.created_at,
                completed_at=test.completed_at,
                feedback=json.loads(test.feedback) if test.feedback else None
            )
            for test in tests
        ]
    )

@router.post("/generate-test", response_model=TestResponse)
async def generate_test(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY is not set in environment variables!")
        raise HTTPException(
            status_code=500,
            detail="OpenRouter API key is not configured"
        )
    from auth.models import User
    user = db.query(User).filter(User.email == current_user["username"]).first()
    if not user:
        logger.error(f"User not found: {current_user['username']}")
        raise HTTPException(status_code=404, detail="User not found")

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "openai/gpt-3.5-turbo",
        "messages": [{"role": "user", "content": CRITICAL_THINKING_PROMPT}],
        "temperature": 0.7,
        "max_tokens": 2000
    }

    logger.info(f"Sending payload to OpenRouter:\n{json.dumps(payload, indent=2)}")

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=30)
        logger.info(f"OpenRouter response status code: {response.status_code}")
        logger.info(f"OpenRouter response text:\n{response.text}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to OpenRouter failed: {e}")
        raise HTTPException(status_code=502, detail="Failed to communicate with OpenRouter API")

    if response.status_code != 200:
        logger.error(f"OpenRouter API returned error status: {response.status_code}")
        raise HTTPException(status_code=response.status_code, detail="OpenRouter API error")

    try:
        data = response.json()
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON response: {e}")
        raise HTTPException(status_code=422, detail="Invalid JSON response from OpenRouter")

    try:
        content_str = data["choices"][0]["message"]["content"]
        logger.info(f"Raw OpenRouter content:\n{content_str}")

        json_str = extract_json_from_string(content_str)
        if not json_str:
            raise ValueError("No JSON found in OpenRouter response content")

        content_json = json.loads(json_str)
    except (KeyError, IndexError, json.JSONDecodeError, ValueError) as e:
        logger.error(f"Response content missing or malformed: {e}")
        raise HTTPException(status_code=422, detail="Malformed response content from OpenRouter")

    if not isinstance(content_json.get("questions"), list):
        logger.error(f"Questions field missing or not a list in response: {content_json}")
        raise HTTPException(status_code=422, detail="Invalid questions format in response")

    questions = []
    for idx, q in enumerate(content_json["questions"], 1):
        if not all(k in q for k in ["text", "options", "correct_index"]):
            logger.error(f"Question missing required fields: {q}")
            raise HTTPException(status_code=422, detail="Question missing required fields")
        questions.append(Question(
            id=idx,
            text=q["text"],
            options=q["options"],
            correct_index=q["correct_index"],
            explanation=q.get("explanation", "")
        ))

    try:
        test = Test(
            user_id=user.id,
            questions=[q.dict() for q in questions],
            created_at= datetime.utcnow(),
        )
        db.add(test)
        db.commit()
        db.refresh(test)
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save test in database: {e}")
        raise HTTPException(status_code=500, detail="Failed to save test")

    logger.info(f"Test generated successfully with ID: {test.id}")

    return TestResponse(
        questions=questions,
        test_id=test.id,
    )


async def generate_ai_feedback(score: float, questions: List[dict], answers: Dict[int, int]) -> dict:
    if not OPENROUTER_API_KEY:
        return {
            "overview": "Feedback service currently unavailable.",
            "strengths": [],
            "improvements": []
        }

    question_summaries = ""
    for q in questions:
        qid = q["id"]
        user_answer = answers.get(qid, -1)
        correct = q["correct_index"]
        explanation = q.get("explanation", "No explanation provided.")
        question_summaries += (
            f"\n\nQ{qid}: {q['text']}\n"
            f"- User Answer: {q['options'][user_answer] if 0 <= user_answer < len(q['options']) else 'Invalid'}\n"
            f"- Correct Answer: {q['options'][correct]}\n"
            f"- Explanation: {explanation}\n"
            f"- Result: {'Correct' if user_answer == correct else 'Incorrect'}"
        )

    prompt = f"""
You are an expert educational psychologist. Return JSON-formatted structured feedback:

{{
    "overview": "summary of critical thinking skills",
    "strengths": ["strength1", "strength2"],
    "improvements": ["improvement1", "improvement2"]
}}

Score: {score} out of 100
Details: {question_summaries}
"""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 800
            },
            timeout=30
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        json_str = extract_json_from_string(content)
        return json.loads(json_str) if json_str else {
            "overview": "Could not parse feedback",
            "strengths": [],
            "improvements": []
        }
    except Exception as e:
        logger.error(f"Failed to generate AI feedback: {e}")
        return {
            "overview": "Feedback generation failed",
            "strengths": [],
            "improvements": []
        }


@router.post("/evaluate-test", response_model=EvaluationResponse)
async def evaluate_test(
    request: EvaluationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from auth.models import User
    user = db.query(User).filter(User.email == current_user["username"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    test = db.query(Test).filter(
        Test.id == request.test_id,
        Test.user_id == user.id
    ).first()
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    try:
        int_answers = {int(k): v for k, v in request.answers.items()}
        score = scorer.calculate_score(test.questions, int_answers)
        
        duration = (datetime.utcnow() - test.created_at).total_seconds() if test.created_at else 600
        rule_strength = strength_evaluator.predict_rule_strength(score, duration)
        ml_strength = strength_evaluator.predict_ml_strength(score, duration)

        ai_feedback = await generate_ai_feedback(score, test.questions, int_answers)

        test.answers = int_answers
        test.score = score
        test.rule_based_strength = rule_strength
        test.ml_based_strength = ml_strength
        test.feedback = json.dumps(ai_feedback)
        test.completed_at = datetime.utcnow()
        db.commit()

        return EvaluationResponse(
            score={
                "value": score,
                "max": 100,
                "percentage": score,
                "rule_based_strength": rule_strength,
                "ml_based_strength": ml_strength
            },
            feedback=ai_feedback,
            detailed_feedback={
                q["id"]: f"Your answer: {q['options'][int_answers.get(q['id'], -1)]}. Correct: {q['options'][q['correct_index']]}"
                for q in test.questions
            }
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Evaluation failed: {e}")
        raise HTTPException(status_code=400, detail=str(e))