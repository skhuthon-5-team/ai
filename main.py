import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY or API_KEY environment variable is required.")

client = genai.Client(api_key=API_KEY)
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")

app = FastAPI(title="Failure AI Analysis API")


class FailureAnalysisRequest(BaseModel):
    failureId: int | None = None
    userId: int | None = None
    title: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    situation: str = Field(..., min_length=1)
    choice: str = Field(..., min_length=1)


def to_json_text(data: BaseModel) -> str:
    return json.dumps(
        data.model_dump(exclude_none=True),
        ensure_ascii=False,
        indent=2,
    )


def parse_json_response(text: str) -> dict:
    cleaned = text.strip()

    if cleaned.startswith("```json"):
        cleaned = cleaned.removeprefix("```json").strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.removeprefix("```").strip()
    if cleaned.endswith("```"):
        cleaned = cleaned.removesuffix("```").strip()

    return json.loads(cleaned)


def generate_json(system_prompt: str, user_content: str) -> dict:
    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=user_content,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        ),
    )

    if not response.text:
        raise ValueError("Gemini returned an empty response.")

    return parse_json_response(response.text)


@app.get("/")
def root():
    return {"message": "Failure AI Analysis Server Running"}


@app.post("/failure-analysis")
def analyze_failure(req: FailureAnalysisRequest):
    system_prompt = """
You write the AI failure analysis shown on a failure detail page.

Input fields:
- title: failure title
- category: failure category
- situation: what happened
- choice: what the user chose or did at that moment

Writing rules:
- Write each value in 1-2 concise Korean sentences.
- Do not blame or judge the user.
- Do not invent facts that are not present in the input.
- Focus only on the failure cause and the next concrete action.

Output rules:
Return only JSON with this exact shape.

{
  "cause": "AI-analyzed reason for the failure",
  "nextAction": "Concrete next action the user can try"
}
"""

    try:
        user_content = f"""
[Failure]
{to_json_text(req)}
"""
        return generate_json(system_prompt, user_content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
