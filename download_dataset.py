"""Nemotron-Personas-Korea (100만 건) 데이터셋을 다운로드하고 CSV로 저장하는 스크립트.

사용법:
    uv run download_dataset.py

동작:
    1. Hugging Face Hub에서 `data/train-0000X-of-00009.parquet` 9개 샤드를 다운로드
    2. 각 샤드를 청크 단위로 읽어 단일 CSV 파일로 스트리밍 저장
       (메모리 사용을 최소화하기 위해 iter_batches 사용)
    3. 결과: data/nemotron_personas_korea.csv
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

REPO_ID = "nvidia/Nemotron-Personas-Korea"
REPO_TYPE = "dataset"
NUM_SHARDS = 9
BATCH_SIZE = 5_000

BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / ".hf_cache"
OUT_DIR = BASE_DIR / "data"
OUT_CSV = OUT_DIR / "nemotron_personas_korea.csv"


def download_shards() -> list[Path]:
    """parquet 샤드를 로컬 캐시로 다운로드하고 경로 목록을 반환한다."""
    paths: list[Path] = []
    for i in range(NUM_SHARDS):
        filename = f"data/train-{i:05d}-of-{NUM_SHARDS:05d}.parquet"
        print(f"  ↓ {filename}")
        local = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            repo_type=REPO_TYPE,
            cache_dir=CACHE_DIR,
            force_download=False,
        )
        paths.append(Path(local))
    return paths


def convert_to_csv(shard_paths: list[Path]) -> None:
    """샤드들을 순서대로 읽어 하나의 CSV로 저장한다."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    writer = None
    total_rows = 0
    fout = OUT_CSV.open("w", newline="", encoding="utf-8-sig")

    try:
        for shard in shard_paths:
            pf = pq.ParquetFile(shard)
            columns = pf.schema_arrow.names

            if writer is None:
                writer = csv.writer(fout, quoting=csv.QUOTE_MINIMAL)
                writer.writerow(columns)

            for batch in pf.iter_batches(batch_size=BATCH_SIZE):
                rows = batch.to_pylist()
                writer.writerows(
                    [
                        [
                            "" if row.get(col) is None else row.get(col)
                            for col in columns
                        ]
                        for row in rows
                    ]
                )
                total_rows += len(rows)
                print(
                    f"\r  → CSV 변환: {total_rows:,} / 1,000,000 행",
                    end="",
                    flush=True,
                )
    finally:
        fout.close()

    print(f"\n  ✓ 완료: {total_rows:,} 행")
    size_mb = OUT_CSV.stat().st_size / 1e6
    print(f"  ✓ 파일: {OUT_CSV}  ({size_mb:,.1f} MB)")


def main() -> int:
    print(f"데이터셋: {REPO_ID}")
    print(f"캐시:    {CACHE_DIR}")
    print(f"출력:    {OUT_CSV}\n")

    shard_paths = download_shards()
    convert_to_csv(shard_paths)

    # 임시 다운로드 캐시 정리 (원본 parquet는 캐시에 남겨두고 싶으면 주석 처리)
    # shutil.rmtree(CACHE_DIR, ignore_errors=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
