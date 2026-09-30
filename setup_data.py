"""배포용: parquet 샤드를 data/parquet 에 직접 다운로드.

ETL(load_data.py)이 data/parquet/*.parquet 를 읽으므로,
배포 환경에서 데이터를 준비하기 위한 스크립트.

사용법:
    uv run setup_data.py
    # 또는
    .venv/bin/python setup_data.py
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from huggingface_hub import hf_hub_download

REPO_ID = "nvidia/Nemotron-Personas-Korea"
NUM_SHARDS = 9
BASE_DIR = Path(__file__).resolve().parent
CACHE_DIR = BASE_DIR / ".hf_cache"
OUT_DIR = BASE_DIR / "data" / "parquet"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for i in range(NUM_SHARDS):
        filename = f"data/train-{i:05d}-of-{NUM_SHARDS:05d}.parquet"
        print(f"[setup] ↓ {filename}")
        local = hf_hub_download(
            repo_id=REPO_ID,
            filename=filename,
            repo_type="dataset",
            cache_dir=CACHE_DIR,
            force_download=False,
        )
        target = OUT_DIR / f"train-{i:05d}-of-{NUM_SHARDS:05d}.parquet"
        if not target.exists():
            shutil.copy2(local, target)
            print(f"[setup]   → {target}")
        else:
            print(f"[setup]   이미 존재: {target}")

    print(f"[setup] 완료. {OUT_DIR} 에 {NUM_SHARDS}개 parquet 준비됨.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
