import requests

api_key = "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"
url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

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

payload = {
    "model": "qwen/qwen-2.5-72b-instruct:free",
    "messages": [
        {"role": "user", "content": CRITICAL_THINKING_PROMPT}
    ]
}

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(response.json())
