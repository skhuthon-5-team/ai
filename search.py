import json
import math
from pathlib import Path
from typing import Any

import chromadb

from embedding import get_embedding, make_case_text

BASE_DIR = Path(__file__).resolve().parent
CASES_PATH = BASE_DIR / "cases.json"
DB_PATH = BASE_DIR / ".chroma_db"
COLLECTION_NAME = "failure_cases"


def load_cases() -> list[dict[str, Any]]:
    with CASES_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def get_collection():
    chroma_client = chromadb.PersistentClient(path=str(DB_PATH))
    return chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def case_id(case: dict[str, Any]) -> str:
    value = case.get("failureId") or case.get("id")
    return str(value) if value is not None else ""


def reset_index() -> dict[str, int]:
    cases = load_cases()
    collection = get_collection()

    existing = collection.get()
    if existing.get("ids"):
        collection.delete(ids=existing["ids"])

    ids = [case_id(case) for case in cases]
    documents = [make_case_text(case) for case in cases]
    embeddings = [get_embedding(document) for document in documents]
    metadatas = [
        {
            "id": case_id(case),
            "title": case.get("title", ""),
            "category": case.get("category", ""),
        }
        for case in cases
    ]

    collection.add(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )

    return {"indexed_count": len(cases)}


def to_recommendation(case: dict[str, Any], similarity: float | None = None) -> dict[str, Any]:
    recommendation = {
        "failureId": case.get("failureId") or case.get("id"),
        "title": case.get("title", ""),
        "category": case.get("category", ""),
        "situation": case.get("situation") or case.get("content", ""),
        "choice": case.get("choice", ""),
        "cause": case.get("cause", ""),
        "nextAction": case.get("nextAction", ""),
        "writer": case.get("writer", ""),
        "createdAt": case.get("createdAt"),
    }

    if similarity is not None:
        recommendation["similarity"] = round(similarity, 4)

    return recommendation


def recommend_cases(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    collection = get_collection()

    if collection.count() == 0:
        reset_index()

    query_embedding = get_embedding(query)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    cases_by_id = {case_id(case): case for case in load_cases()}
    recommendations = []

    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]

    for item_id, distance in zip(ids, distances):
        case = cases_by_id.get(str(item_id))
        if not case:
            continue

        recommendations.append(to_recommendation(case, 1 - float(distance)))

    return recommendations


def cosine_similarity(left: list[float], right: list[float]) -> float:
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot / (left_norm * right_norm)


def recommend_from_failures(
    target: dict[str, Any],
    failures: list[dict[str, Any]],
    top_k: int = 3,
) -> list[dict[str, Any]]:
    target_id = case_id(target)
    target_embedding = get_embedding(make_case_text(target))

    scored_cases = []
    for failure in failures:
        if target_id and case_id(failure) == target_id:
            continue

        failure_embedding = get_embedding(make_case_text(failure))
        scored_cases.append(
            (
                cosine_similarity(target_embedding, failure_embedding),
                failure,
            )
        )

    scored_cases.sort(key=lambda item: item[0], reverse=True)

    return [
        to_recommendation(failure, similarity)
        for similarity, failure in scored_cases[:top_k]
    ]
