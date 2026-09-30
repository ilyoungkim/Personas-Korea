"""③ Embedding + Qdrant (청크 스트리밍, 대규모 대응).

메모리 사용을 일정하게 유지하기 위해 전체를 한 번에 올리지 않고,
CHUNK_SIZE 단위로 PostgreSQL 읽기 → 임베딩 → Qdrant 적재를 반복합니다.
1M 건도 OOM 없이 처리 가능.

사용법:
    python embed_poc.py
    (환경변수 EMBED_N 으로 건수, CHUNK_SIZE 로 청크 크기 지정)
"""

import os
import time

import psycopg
from psycopg.rows import dict_row
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from sentence_transformers import SentenceTransformer

PG_DSN = os.getenv("PG_DSN", "postgresql://persona:persona@postgres:5432/persona")
QDRANT_URL = os.getenv("QDRANT_URL", "http://qdrant:6333")
COLLECTION = "persona"
MODEL_NAME = os.getenv("EMBED_MODEL", "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
SAMPLE_N = int(os.getenv("EMBED_N", "10000"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "5000"))
BATCH = 500


def _text(r: dict) -> str:
    return (
        (r["sex"] or "") + " " + str(r["age"] or "") + "세 " +
        (r["province"] or "") + " " + (r["district"] or "") + " " +
        (r["occupation"] or "") + " " + (r["persona"] or "")
    )


def main() -> None:
    t_start = time.time()
    print(f"[embed] 모델 로드: {MODEL_NAME}", flush=True)
    model = SentenceTransformer(MODEL_NAME)
    dim = model.get_sentence_embedding_dimension()
    print(f"[embed] 임베딩 차원: {dim}", flush=True)

    client = QdrantClient(url=QDRANT_URL, timeout=120)
    if client.collection_exists(COLLECTION):
        client.delete_collection(COLLECTION)
    client.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
    )

    conn = psycopg.connect(PG_DSN, row_factory=dict_row)
    cur = conn.cursor(name="embed_cursor")
    cur.itersize = CHUNK_SIZE
    cur.execute(
        "SELECT uuid, sex, age, province, district, occupation, family_type, persona "
        f"FROM persona ORDER BY uuid LIMIT {SAMPLE_N}"
    )

    total = 0
    next_id = 0
    while True:
        rows = cur.fetchmany(CHUNK_SIZE)
        if not rows:
            break
        texts = [_text(r) for r in rows]
        vectors = model.encode(texts, show_progress_bar=False, batch_size=64,
                               convert_to_numpy=True)

        points = []
        for i, r in enumerate(rows):
            points.append({
                "id": next_id + i,
                "vector": vectors[i].tolist(),
                "payload": {
                    "uuid": r["uuid"], "sex": r["sex"], "age": r["age"],
                    "province": r["province"], "district": r["district"],
                    "occupation": r["occupation"], "family_type": r["family_type"],
                    "persona": r["persona"],
                },
            })
            if len(points) >= BATCH:
                client.upsert(collection_name=COLLECTION, points=points)
                points = []
        if points:
            client.upsert(collection_name=COLLECTION, points=points)

        next_id += len(rows)
        total += len(rows)
        elapsed = time.time() - t_start
        rate = total / elapsed if elapsed > 0 else 0
        print(f"[embed] {total:,}/{SAMPLE_N:,} 완료 ({rate:.0f}건/초, 경과 {elapsed:.0f}초)", flush=True)

    cur.close()
    conn.close()
    print(f"[embed] 완료. 총 {total:,}건, 소요 {time.time() - t_start:.0f}초")


if __name__ == "__main__":
    main()
