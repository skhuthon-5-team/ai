import os
from typing import Iterable

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY 또는 API_KEY 환경변수를 설정해주세요.")

client = genai.Client(api_key=API_KEY)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")


def get_embedding(text: str) -> list[float]:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("임베딩할 텍스트가 비어 있습니다.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=clean_text,
    )
    return response.embeddings[0].values


def make_case_text(case: dict) -> str:
    title = case.get("title", "")
    category = case.get("category", "")
    situation = case.get("situation") or case.get("content", "")
    choice = case.get("choice") or case.get("cause", "")
    emotion = case.get("emotion", "")
    lesson = case.get("lesson", "")

    return "\n".join(
        [
            f"제목: {title}",
            f"카테고리: {category}",
            f"상황: {situation}",
            f"선택: {choice}",
            f"감정: {emotion}",
            f"교훈: {lesson}",
        ]
    )


def generate_chat_answer(question: str, contexts: Iterable[dict]) -> str:
    context_text = "\n\n".join(
        [
            f"[사례 {idx}]\n"
            f"제목: {case.get('title', '')}\n"
            f"카테고리: {case.get('category', '')}\n"
            f"상황: {case.get('situation') or case.get('content', '')}\n"
            f"선택: {case.get('choice') or case.get('cause', '')}\n"
            f"감정: {case.get('emotion', '')}\n"
            f"교훈: {case.get('lesson', '')}"
            for idx, case in enumerate(contexts, start=1)
        ]
    )

    system_prompt = f"""
너는 실패 사례를 바탕으로 답변하는 상담 챗봇이다.

[답변 규칙]
1. 반드시 아래 [관련 실패 사례]를 근거로 답변한다.
2. 관련 사례에 없는 내용은 추측하지 않는다.
3. 정보가 부족하면 "제공된 실패 사례에서 관련 정보를 충분히 찾을 수 없습니다."라고 말한다.
4. 사용자가 다음 시도를 할 수 있도록 짧고 구체적으로 조언한다.
5. 항상 친절하고 조심스러운 말투로 답변한다.

[관련 실패 사례]
{context_text}
"""

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=question,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text or ""
