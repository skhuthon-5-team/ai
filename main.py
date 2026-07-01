import json
import os
from typing import Literal

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

app = FastAPI(title="AI Growth Report API")


class FailurePost(BaseModel):
    id: int | None = None
    title: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    cause: str | None = None
    feeling: str | None = None
    created_at: str | None = None


class RetryPlan(BaseModel):
    id: int | None = None
    failure_id: int | None = None
    goal: str = Field(..., min_length=1)
    plan: str = Field(..., min_length=1)
    action_items: list[str] = []
    created_at: str | None = None


class ReflectionPost(BaseModel):
    id: int | None = None
    failure_id: int | None = None
    content: str = Field(..., min_length=1)
    result: str | None = None
    learned: str | None = None
    is_success: bool | None = None
    created_at: str | None = None


class GrowthReportRequest(BaseModel):
    user_id: int | None = None
    failure: FailurePost
    retry_plan: RetryPlan | None = None
    reflection: ReflectionPost | None = None
    report_type: Literal["single_failure", "mypage_summary"] = "single_failure"


class GrowthCompareRequest(BaseModel):
    failure: FailurePost
    reflection: ReflectionPost


def to_json_text(data: BaseModel) -> str:
    return json.dumps(
        data.model_dump(),
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
    return {"message": "AI Growth Report Server Running"}


@app.post("/growth-report")
def create_growth_report(req: GrowthReportRequest):
    system_prompt = """
너는 실패 경험을 성장 관점으로 분석하는 AI 코치야.

[역할]
- 사용자가 작성한 실패담, 재도전 계획, 회고록을 바탕으로 성장 리포트를 만든다.
- 사용자를 평가하거나 비난하지 않고, 변화와 배운 점을 구체적으로 정리한다.
- 없는 정보는 지어내지 않는다.

[출력 규칙]
반드시 아래 JSON 형식으로만 답변한다.

{
  "summary": "전체 성장 요약 2~3문장",
  "growth_points": ["성장 포인트 1", "성장 포인트 2", "성장 포인트 3"],
  "before_after": {
    "past": "실패 당시의 모습",
    "present": "현재 변화한 모습",
    "change": "가장 중요한 변화"
  },
  "timeline": [
    {
      "step": "실패",
      "title": "단계 제목",
      "description": "설명"
    },
    {
      "step": "재도전",
      "title": "단계 제목",
      "description": "설명"
    },
    {
      "step": "회고",
      "title": "단계 제목",
      "description": "설명"
    }
  ],
  "next_actions": ["다음 행동 1", "다음 행동 2", "다음 행동 3"],
  "encouragement": "사용자에게 건네는 짧은 응원 문장"
}
"""

    try:
        user_content = f"""
[사용자 기록]
{to_json_text(req)}
"""
        return generate_json(system_prompt, user_content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/compare")
def compare_failure_and_reflection(req: GrowthCompareRequest):
    system_prompt = """
너는 과거 실패와 현재 회고를 비교해 변화 지점을 분석하는 AI야.

[출력 규칙]
반드시 아래 JSON 형식으로만 답변한다.

{
  "past_failure": "과거 실패의 핵심 원인",
  "current_growth": "현재 회고에서 보이는 성장",
  "changed_attitude": "태도나 관점의 변화",
  "changed_action": "행동 방식의 변화",
  "remaining_challenge": "아직 보완하면 좋은 점",
  "one_line_summary": "한 줄 성장 요약"
}
"""

    try:
        user_content = f"""
[비교할 기록]
{to_json_text(req)}
"""
        return generate_json(system_prompt, user_content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
