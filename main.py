from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from embedding import generate_chat_answer
from search import recommend_cases, reset_index

app = FastAPI(title="Failure Similar Case AI API")


class RecommendRequest(BaseModel):
    text: str = Field(..., min_length=1, description="사용자의 실패담 또는 검색 문장")
    top_k: int = Field(3, ge=1, le=10)


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1)
    top_k: int = Field(3, ge=1, le=5)


@app.get("/")
def root():
    return {"message": "Similar Case AI Server Running"}


@app.post("/index")
def index_cases():
    try:
        return reset_index()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/recommend")
def recommend(req: RecommendRequest):
    try:
        return {"recommendations": recommend_cases(req.text, req.top_k)}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/chat")
def chat(req: ChatRequest):
    try:
        contexts = recommend_cases(req.question, req.top_k)
        answer = generate_chat_answer(req.question, contexts)
        return {
            "answer": answer,
            "references": contexts,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
