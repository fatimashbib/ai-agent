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
    "model": "openai/gpt-3.5-turbo",
    "messages": [
        {"role": "user", "content": CRITICAL_THINKING_PROMPT}
    ]
}

response = requests.post(url, headers=headers, json=payload)

print(response.status_code)
print(response.json())

# https://openrouter.ai/settings/keys