CRITICAL_THINKING_PROMPT = """
Generate 5 multiple choice questions that test advanced critical thinking skills.
Each question should:
1. Present a complex scenario or argument
2. Have 4 plausible options
3. Include one clearly correct answer
4. Cover different aspects of critical thinking (logic, assumptions, implications)

Format as JSON with:
{
    "questions": [
        {
            "text": "question text",
            "options": ["a", "b", "c", "d"],
            "correct_index": 0,
            "explanation": "rationale for correct answer",
            "skill": "identified skill being tested"
        }
    ]
}
"""