"""Nemotron-Personas-Korea 100만 건을 PostgreSQL에 적재하는 스크립트.

원본 parquet(9개 샤드)를 청크 단위로 읽어 `persona` 테이블에 COPY로 적재합니다.
region 테이블도 자동으로 채웁니다.

사용법 (컨테이너 내부에서 실행):
    python load_data.py
"""

import os
import time
import uuid as uuid_mod
from pathlib import Path

import pyarrow.parquet as pq
import psycopg
from psycopg import sql

# ---- 설정 (환경변수로 주입) ----
PG_DSN = os.getenv("PG_DSN", "postgresql://persona:persona@postgres:5432/persona")
DATA_DIR = Path(os.getenv("DATA_DIR", "/data"))
BATCH_SIZE = 20_000

COLS = [
    "uuid", "sex", "age", "marital_status", "military_status", "family_type",
    "housing_type", "education_level", "bachelors_field", "occupation",
    "district", "province", "country", "cultural_background",
    "skills_and_expertise", "skills_and_expertise_list", "hobbies_and_interests",
    "hobbies_and_interests_list", "career_goals_and_ambitions", "persona",
    "professional_persona", "sports_persona", "arts_persona", "travel_persona",
    "culinary_persona", "family_persona",
]


def parquet_files() -> list[Path]:
    files = sorted(DATA_DIR.glob("*.parquet"))
    if not files:
        raise FileNotFoundError(f"parquet 없음: {DATA_DIR}")
    return files


def null_to_empty(v):
    return "" if v is None else v


def main() -> None:
    files = parquet_files()
    print(f"[load] parquet {len(files)}개 발견")

    conn = psycopg.connect(PG_DSN, autocommit=False)
    cur = conn.cursor()

    # schema 적용
    for sql_file in ["/app/sql/schema.sql", "/app/sql/indexes.sql"]:
        p = Path(sql_file)
        if p.exists():
            cur.execute(p.read_text(encoding="utf-8"))
            conn.commit()
            print(f"[load] 적용: {sql_file}")

    total = 0
    region_set = set()

    for f in files:
        pf = pq.ParquetFile(f)
        for batch in pf.iter_batches(batch_size=BATCH_SIZE):
            rows = []
            for r in batch.to_pylist():
                rows.append(tuple(null_to_empty(r.get(c)) for c in COLS))
                region_set.add((null_to_empty(r.get("province")),
                                null_to_empty(r.get("district"))))

            with cur.copy(sql.SQL(
                "COPY persona ({}) FROM STDIN".format(", ".join(COLS))
            )) as copy:
                for row in rows:
                    copy.write_row(row)

            conn.commit()
            total += len(rows)
            print(f"[load] 누적 {total:,} 행", flush=True)

    # region 테이블 채우기
    if region_set:
        region_rows = [
            (str(uuid_mod.uuid4()), p, d, "")
            for (p, d) in region_set
            if p or d
        ]
        with cur.copy("COPY region (code, province, district, region_type) FROM STDIN") as copy:
            for row in region_rows:
                copy.write_row(row)
        conn.commit()
        print(f"[load] region {len(region_rows):,} 행 적재")

    cur.execute("SELECT count(*) FROM persona")
    print(f"[load] 완료. persona 총 {cur.fetchone()[0]:,} 행")
    conn.close()


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"[load] 소요 {time.time() - t0:.1f}초")
