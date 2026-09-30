"""Qdrant 의미 검색 계층 (임베딩 내장).

similar_persona 툴이 실제 Qdrant 벡터 검색을 사용하도록 한다.
- 쿼리를 sentence-transformers로 임베딩
- Qdrant 컬렉션에서 코사인 유사도 검색
- Qdrant가 준비되지 않았거나 컬렉션이 없으면 LIKE 폴백
"""

from __future__ import annotations

import os
import sys

import psycopg
from psycopg.rows import dict_row

PG_DSN = os.getenv("PG_DSN", "postgresql://persona:persona@postgres:5432/persona")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION = "persona"
MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")


class SimilarityDB:
    def __init__(self) -> None:
        self._qdrant = None
        self._model = None
        try:
            from qdrant_client import QdrantClient
            self._qdrant = QdrantClient(url=QDRANT_URL, timeout=10)
        except Exception:
            self._qdrant = None

    def _embed(self, text: str) -> list[float]:
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            print(f"[mcp] 임베딩 모델 로드: {MODEL_NAME}", file=sys.stderr, flush=True)
            self._model = SentenceTransformer(MODEL_NAME)
        return self._model.encode(text).tolist()

    def similar(self, query: str, limit: int = 10, filters: dict | None = None) -> dict:
        """자연어 질의 → 유사 페르소나 검색 (Qdrant 벡터 + 조건 필터, 폴백 LIKE).

        filters: payload 조건 (예: {"sex":"여자","province":"경기"}).
                 Qdrant 필터로 결합해 의미 + 조건 하이브리드 검색을 수행.
        """
        if self._qdrant is not None:
            try:
                if self._qdrant.collection_exists(COLLECTION):
                    info = self._qdrant.get_collection(COLLECTION)
                    if info.points_count > 0:
                        return self._qdrant_similar(query, limit, filters)
            except Exception as e:
                print(f"[mcp] Qdrant 검색 실패, LIKE 폴백: {e}", file=sys.stderr, flush=True)
        return self._like_fallback(query, limit, filters)

    def _build_filter(self, filters: dict | None):
        """payload 필터 dict → Qdrant Filter 객체."""
        if not filters:
            return None
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        conditions = []
        for key, val in filters.items():
            if val is None or val == "":
                continue
            conditions.append(
                FieldCondition(key=key, match=MatchValue(value=val))
            )
        if not conditions:
            return None
        return Filter(must=conditions)

    def _qdrant_similar(self, query: str, limit: int, filters: dict | None = None) -> dict:
        vector = self._embed(query)
        qfilter = self._build_filter(filters)
        hits = self._qdrant.search(
            collection_name=COLLECTION,
            query_vector=vector,
            limit=limit,
            query_filter=qfilter,
        )
        results = [
            {
                "score": round(h.score, 4),
                "uuid": h.payload.get("uuid"),
                "sex": h.payload.get("sex"),
                "age": h.payload.get("age"),
                "province": h.payload.get("province"),
                "district": h.payload.get("district"),
                "occupation": h.payload.get("occupation"),
                "family_type": h.payload.get("family_type"),
                "persona": h.payload.get("persona"),
            }
            for h in hits
        ]
        return {"engine": "qdrant", "query": query, "filters": filters, "results": results}

    def _like_fallback(self, query: str, limit: int, filters: dict | None = None) -> dict:
        tokens = [t for t in query.replace(",", " ").split() if len(t) >= 2]
        if not tokens:
            return {"engine": "like", "query": query, "results": []}
        patterns = [f"%{t}%" for t in tokens]
        where = ["(hobbies_and_interests ILIKE ANY(%s) OR persona ILIKE ANY(%s))"]
        params: list = [patterns, patterns]
        for key, val in (filters or {}).items():
            if val is None or val == "":
                continue
            where.append(f"{key} = %s")
            params.append(val)
        q = (
            "SELECT uuid, sex, age, province, district, occupation, persona "
            "FROM persona WHERE " + " AND ".join(where) +
            " LIMIT " + str(int(limit))
        )
        try:
            with psycopg.connect(PG_DSN, row_factory=dict_row) as conn:
                rows = conn.execute(q, params).fetchall()
            return {"engine": "like", "query": query, "filters": filters, "results": rows}
        except Exception as e:
            return {"engine": "like", "query": query, "results": [], "error": str(e)}
