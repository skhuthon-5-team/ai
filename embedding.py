import os
from typing import Iterable

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("API_KEY")

if not API_KEY:
    raise RuntimeError("GOOGLE_API_KEY or API_KEY environment variable is required.")

client = genai.Client(api_key=API_KEY)

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")
CHAT_MODEL = os.getenv("CHAT_MODEL", "gemini-2.5-flash")


def get_embedding(text: str) -> list[float]:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("Text to embed must not be empty.")

    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=clean_text,
    )
    return response.embeddings[0].values


def make_case_text(case: dict) -> str:
    title = case.get("title", "")
    category = case.get("category", "")
    situation = case.get("situation") or case.get("content", "")
    choice = case.get("choice", "")
    cause = case.get("cause", "")
    next_action = case.get("nextAction", "")
    lesson = case.get("lesson", "")

    return "\n".join(
        [
            f"Title: {title}",
            f"Category: {category}",
            f"Situation: {situation}",
            f"Choice: {choice}",
            f"Cause: {cause}",
            f"Next action: {next_action}",
            f"Lesson: {lesson}",
        ]
    )


def generate_chat_answer(question: str, contexts: Iterable[dict]) -> str:
    context_text = "\n\n".join(
        [
            f"[Case {idx}]\n"
            f"Title: {case.get('title', '')}\n"
            f"Category: {case.get('category', '')}\n"
            f"Situation: {case.get('situation') or case.get('content', '')}\n"
            f"Choice: {case.get('choice', '')}\n"
            f"Cause: {case.get('cause', '')}\n"
            f"Next action: {case.get('nextAction', '')}\n"
            f"Lesson: {case.get('lesson', '')}"
            for idx, case in enumerate(contexts, start=1)
        ]
    )

    system_prompt = f"""
You are a helpful assistant that answers based on failure cases.

Rules:
1. Answer only from the related failure cases below.
2. Do not invent facts that are not present in the cases.
3. If there is not enough information, say that the provided failure cases do not contain enough related information.
4. Give concrete advice for the user's next attempt.
5. Answer politely in Korean.

[Related failure cases]
{context_text}
"""

    response = client.models.generate_content(
        model=CHAT_MODEL,
        contents=question,
        config=types.GenerateContentConfig(system_instruction=system_prompt),
    )
    return response.text or ""
