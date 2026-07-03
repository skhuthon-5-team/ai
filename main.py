from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from embedding import generate_chat_answer
from search import recommend_cases, recommend_from_failures, reset_index

app = FastAPI(title="Failure Similar Case AI API")


class FailureItem(BaseModel):
    failureId: int | None = None
    id: int | None = None
    userId: int | None = None
    title: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1)
    situation: str = Field(..., min_length=1)
    choice: str = Field(..., min_length=1)
    emotion: str | None = None
    writer: str | None = None
    createdAt: str | None = None
    updatedAt: str | None = None


class RecommendRequest(BaseModel):
    text: str = Field(..., min_length=1, description="검색할 실패담 문장")
    top_k: int = Field(3, ge=1, le=10)


class RecommendFromFailuresRequest(BaseModel):
    target: FailureItem
    failures: list[FailureItem] = Field(..., min_length=1)
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


@app.post("/recommend/from-failures")
def recommend_from_backend_failures(req: RecommendFromFailuresRequest):
    try:
        target = req.target.model_dump(exclude_none=True)
        failures = [failure.model_dump(exclude_none=True) for failure in req.failures]

        return {
            "recommendations": recommend_from_failures(
                target=target,
                failures=failures,
                top_k=req.top_k,
            )
        }
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
