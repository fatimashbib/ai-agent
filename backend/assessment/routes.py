import regex as re
import json
import os
import logging
from datetime import datetime
from typing import Optional, Dict, List

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .scoring import Scorer
from .prompts import CRITICAL_THINKING_PROMPT
from database.session import get_db
from auth.security import get_current_user
from assessment.models.test import Test
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  # or DEBUG for more details

router = APIRouter(
    tags=["assessment"],
    responses={404: {"description": "Not found"}}
)

load_dotenv()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")
scorer = Scorer()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class Question(BaseModel):
    id: int
    text: str
    options: List[str]
    correct_index: int  # add this
    explanation: Optional[str] = None


class TestResponse(BaseModel):
    questions: List[Question]
    test_id: int


class EvaluationRequest(BaseModel):
    test_id: int
    answers: Dict[str, int]  # Fix: string keys

class EvaluationResponse(BaseModel):
    rule_based: Dict[str, float]
    ml_based: Dict[str, float]
    feedback: str
    detailed_feedback: Optional[Dict[int, str]] = None


def extract_json_from_string(text: str) -> Optional[str]:
    """
    Extract the first JSON object from a text string.
    Uses balanced braces recursion pattern.
    """
    json_match = re.search(r"\{(?:[^{}]|(?R))*\}", text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    return None


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
    
    # Import User model here to avoid circular imports if any
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
        "model": "qwen/qwen-2.5-72b-instruct:free",
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
    
    # Extract JSON string inside the content field
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
            correct_index=q["correct_index"],  # <--- add this!
            explanation=q.get("explanation", "")
        ))
    
    # Save test in DB
    try:
        test = Test(
            user_id=user.id,
            questions=[q.dict() for q in questions],
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

async def generate_ai_feedback(rule_score: float, ml_score: float, questions: List[dict], answers: Dict[int, int]) -> str:
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter API key is not configured")
        return "Feedback service currently unavailable."

    # Create a contextual breakdown of each question
    question_summaries = ""
    for q in questions:
        qid = q["id"]
        user_answer = answers.get(qid, -1)
        correct = q["correct_index"]
        is_correct = user_answer == correct
        explanation = q.get("explanation", "No explanation provided.")
        question_summaries += (
            f"\n\nQ{qid}: {q['text']}\n"
            f"- User Answer: {q['options'][user_answer] if 0 <= user_answer < len(q['options']) else 'Invalid'}\n"
            f"- Correct Answer: {q['options'][correct]}\n"
            f"- Explanation: {explanation}\n"
            f"- Result: {'Correct' if is_correct else 'Incorrect'}"
        )

    prompt = f"""
You are an expert educational psychologist. Based on the test results, generate a detailed, clear, and constructive feedback report on a test taker's critical thinking skills.

Scores:
- Rule-based score: {rule_score} out of 100
- ML-based score: {ml_score} out of 10

Details:
{question_summaries}

Feedback should include:
1. Overview of overall performance
2. Strengths (numbered bullets)
3. Areas for improvement (numbered bullets)
4. Format in markdown

Be encouraging and insightful.
"""

    payload = {
        "model": "qwen/qwen-2.5-72b-instruct:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": 800
    }

    try:
        response = requests.post(OPENROUTER_URL, headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }, json=payload, timeout=30)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"Failed to generate AI feedback: {e}", exc_info=True)
        return "Could not generate AI feedback at this time. Please try again later."

@router.post("/evaluate-test", response_model=EvaluationResponse)
async def evaluate_test(
    request: EvaluationRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    logger.info(f"Evaluating test ID: {request.test_id}")
    from auth.models import User
    user = db.query(User).filter(User.email == current_user["username"]).first()
    if not user:
        logger.error(f"User not found: {current_user['username']}")
        raise HTTPException(status_code=404, detail="User not found")

    test = db.query(Test).filter(
        Test.id == request.test_id,
        Test.user_id == user.id
    ).first()

    if not test:
        logger.error(f"Test not found or access denied: {request.test_id}")
        raise HTTPException(status_code=404, detail="Test not found or access denied")

    try:
        int_answers = {int(k): v for k, v in request.answers.items()}

        for qid, ans_idx in int_answers.items():
            question = next((q for q in test.questions if q["id"] == qid), None)
            if question is None:
                raise ValueError(f"Question ID {qid} not found in test")
            if not (0 <= ans_idx < len(question["options"])):
                raise ValueError(f"Answer index {ans_idx} out of range for question ID {qid}")

        logger.info("Calculating scores")
        rule_score = scorer.rule_based_score(test.questions, int_answers)
        ml_score = scorer.ml_based_score(test.questions, int_answers)

        detailed_feedback = {
            q["id"]: (
                f"Your answer: {q['options'][int_answers.get(q['id'], -1)]}. "
                f"Correct answer: {q['options'][q['correct_index']]}"
            )
            for q in test.questions
        }

        logger.info("Generating AI feedback")
        ai_feedback = await generate_ai_feedback(rule_score, ml_score, test.questions, int_answers)

        logger.info("Updating test record with evaluation results")
        test.answers = int_answers
        test.rule_based_score = rule_score
        test.ml_based_score = ml_score
        test.feedback = ai_feedback
        test.completed_at = datetime.utcnow()

        db.commit()

        logger.info(f"Successfully evaluated test ID: {test.id}")
        return EvaluationResponse(
            rule_based={
                "score": round(rule_score, 1),
                "max": 100,
                "percentage": round(rule_score, 1),
            },
            ml_based={
                "score": round(ml_score, 1),
                "max": 10,
                "percentage": round(ml_score * 10, 1),
            },
            feedback=ai_feedback,
            detailed_feedback=detailed_feedback
        )

    except Exception as e:
        db.rollback()
        logger.error(f"Evaluation failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="Evaluation failed due to invalid data")
