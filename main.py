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
    raise RuntimeError("GOOGLE_API_KEY 또는 API_KEY 환경변수를 설정해주세요.")

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
    emotion: str | None = None


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
        raise ValueError("Gemini 응답이 비어 있습니다.")

    return parse_json_response(response.text)


@app.get("/")
def root():
    return {"message": "Failure AI Analysis Server Running"}


@app.post("/failure-analysis")
def analyze_failure(req: FailureAnalysisRequest):
    system_prompt = """
너는 실패담 상세 페이지의 'AI 실패 분석' 카드에 들어갈 짧은 문장을 작성하는 AI다.

[입력 데이터]
- title: 실패담 제목
- category: 실패담 카테고리(EMPLOYMENT, STUDY, LOVE, RELATIONSHIP, STARTUP, ETC)
- situation: 실패가 발생한 상황
- choice: 당시 사용자가 한 선택이나 대응
- emotion: 당시 감정

[작성 규칙]
- 화면 카드에 들어갈 내용이므로 각 항목은 1~2문장으로 짧게 작성한다.
- 사용자를 비난하거나 단정하지 않는다.
- 입력에 없는 사실은 지어내지 않는다.
- 너무 거창한 성장 리포트가 아니라, 실패 원인/교훈/다음 전략만 정리한다.

[출력 규칙]
반드시 아래 JSON 형식으로만 응답한다.

{
  "cause": "AI가 분석한 실패 원인",
  "lesson": "이번 실패에서 얻은 교훈",
  "strategy": "다음 도전 전략"
}
"""

    try:
        user_content = f"""
[실패담]
{to_json_text(req)}
"""
        return generate_json(system_prompt, user_content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
