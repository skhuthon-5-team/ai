import json
import os
from pathlib import Path

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
app = FastAPI(title="Failure Chatbot API")

BASE_DIR = Path(__file__).resolve().parent
FAILURES_PATH = BASE_DIR / "failures.json"


def load_failures() -> list[dict]:
    with FAILURES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_system_prompt() -> str:
    failure_text = ""

    for idx, item in enumerate(load_failures(), start=1):
        failure_text += f"""
사례 {idx}
제목: {item.get("title", "")}
내용: {item.get("content", "")}
"""

    return f"""
너는 실패 사례 분석 AI 챗봇이야.

[답변 규칙]
1. 반드시 아래 [실패 사례]를 기반해서 답변한다.
2. 만약 [실패 사례] 내용으로 답변할 수 없거나 없는 정보라면, 추측하지 말고 "제공된 문서에서 관련 정보를 찾을 수 없습니다."라고 정중하게 답변한다.
3. 말투는 항상 친절하고 상냥한 존댓말을 사용하여 답변한다.

[실패 사례]
{failure_text}
"""


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)


@app.get("/")
def root():
    return {"message": "AI Server Running"}


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        response = client.models.generate_content(
            model=os.getenv("CHAT_MODEL", "gemini-2.5-flash"),
            contents=req.question,
            config=types.GenerateContentConfig(
                system_instruction=build_system_prompt()
            ),
        )
        return {"answer": response.text}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


