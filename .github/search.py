import json
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


def reset_index() -> dict[str, int]:
    cases = load_cases()
    collection = get_collection()

    existing = collection.get()
    if existing.get("ids"):
        collection.delete(ids=existing["ids"])

    ids = [str(case["id"]) for case in cases]
    documents = [make_case_text(case) for case in cases]
    embeddings = [get_embedding(document) for document in documents]
    metadatas = [
        {
            "id": case["id"],
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


def recommend_cases(query: str, top_k: int = 3) -> list[dict[str, Any]]:
    collection = get_collection()

    if collection.count() == 0:
        reset_index()

    query_embedding = get_embedding(query)
    result = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )

    cases_by_id = {str(case["id"]): case for case in load_cases()}
    recommendations = []

    ids = result.get("ids", [[]])[0]
    distances = result.get("distances", [[]])[0]

    for case_id, distance in zip(ids, distances):
        case = cases_by_id.get(str(case_id))
        if not case:
            continue

        recommendations.append(
            {
                "id": case["id"],
                "title": case.get("title", ""),
                "category": case.get("category", ""),
                "content": case.get("content", ""),
                "cause": case.get("cause", ""),
                "lesson": case.get("lesson", ""),
                "similarity": round(1 - float(distance), 4),
            }
        )

    return recommendations
