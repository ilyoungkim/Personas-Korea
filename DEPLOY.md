# Korea Persona Intelligence — 배포 가이드

100만 한국 합성 페르소나 데이터(`nvidia/Nemotron-Personas-Korea`)를
PostgreSQL + Qdrant + MCP + Nuxt 대시보드로 서비스하는 시스템의 배포판입니다.

> 전체 아키텍처와 개발 계획은 `plan.md`, 일반 사용법은 `README.md` 참조.

---

## 1. 사전 요구사항

- Docker (Docker Compose v2 이상)
- 인터넷 연결 (데이터셋 다운로드, Hugging Face 접근)
- Python 3.13 (데이터 준비 스크립트 실행 시)
- 디스크 여유 공간: 최소 **8GB** (parquet 2GB + PostgreSQL 데이터 + Docker 이미지)

---

## 2. 설치 절차

### 2.1 압축 해제

```bash
tar -xzf persona-korea.tar.gz
cd persona-korea
```

### 2.2 데이터 준비 (최초 1회)

원본 parquet 샤드 9개를 `data/parquet/` 에 다운로드합니다.

```bash
# 방법 A: 로컬에 Python + huggingface_hub 설치 후
uv add huggingface_hub pyarrow
uv run setup_data.py

# 방법 B: 도커로 (etl 이미지 재사용)
docker compose run --rm -v "$PWD/data:/data" etl bash -c "python setup_data.py"
```

> 또는 기존 CSV/parquet가 있다면 `data/parquet/*.parquet` 로 직접 배치해도 됩니다.

### 2.3 전체 서비스 기동

```bash
docker compose up -d --build
```

이렇게 하면 4개 서비스가 기동됩니다:

| 서비스 | 포트 |
|---|---|
| postgres | 15432 |
| qdrant | 16333/16334 |
| mcp | 19000 |
| dashboard | 18080 |

### 2.4 데이터 적재 (최초 1회, 100만 건)

```bash
docker compose run --rm etl
```

약 10분 소요 (환경에 따라 다름).

### 2.5 (선택) 임베딩 → Qdrant 의미 검색

```bash
# 300,000건 (30% 커버리지, 약 2시간 소요)
docker compose run --rm -e EMBED_N=300000 -e CHUNK_SIZE=5000 embed
```

> 임베딩은 CPU 기반으로 시간이 오래 걸립니다. 의미 검색을 안 쓸 경우 생략 가능하며,
> 이 경우 `similar_persona`는 LIKE 키워드 검색으로 폴백 동작합니다.

### 2.6 (선택) Core Persona 별칭 생성

```bash
# 1) 예제 파일을 key.txt 로 복사
cp key.txt.example key.txt

# 2) key.txt 안의 sk-or-v1-... 부분을 실제 OpenRouter API 키로 교체

# 3) 실행
uv run etl/generate_aliases.py
```

> 생략 시 규칙 기반 라벨("수도권 무직" 등)이 그대로 사용됩니다.

---

## 3. 접속

| 서비스 | URL |
|---|---|
| 대시보드 | `http://<호스트IP>:18080` |
| MCP Server | `http://<호스트IP>:19000/mcp` |
| PostgreSQL | `postgresql://persona:persona@<호스트IP>:15432/persona` |
| Qdrant | `http://<호스트IP>:16333` |

> 호스트 IP는 `ifconfig`/`ipconfig`로 확인. 로컬 192.168.x.x 대역에서 사용 권장.

---

## 4. ChatGPT 연결

원격 URL 등록 (streamable-http):

```
http://<호스트IP>:19000/mcp
```

또는 `mcp-config.json` 내용을 클라이언트 설정에 복사.

---

## 5. 종료 / 재시작

```bash
docker compose down        # 컨테이너만 중지
docker compose down -v     # 데이터 볼륨까지 삭제 (주의)
docker compose up -d       # 재시작
```

---

## 6. 패키지 구성 (대용량 데이터 제외)

배포 패키지는 **코드·설정·문서만 포함**하며, 대용량 데이터는 제외됩니다:

```
persona-korea/
├── docker-compose.yml
├── README.md / plan.md
├── setup_data.py / download_dataset.py
├── key.txt.example (OpenRouter API 키 예제 — 실제 key.txt는 제외됨)
├── mcp-config.json
├── sql/          (schema.sql, indexes.sql, clustering.sql 등)
├── etl/          (load_data.py, embed_poc.py, generate_aliases.py)
├── mcp/          (server.py, db/, requirements.txt, Dockerfile)
├── dashboard/    (Nuxt 소스 + Dockerfile)
├── embed/        (임베딩 Dockerfile)
└── data/parquet/ (비어 있음 — setup_data.py 로 채움)
```

제외된 대용량 파일:
- `data/nemotron_personas_korea.csv` (3.9GB)
- `data/parquet/*.parquet` (1.8GB)
- `.hf_cache/` (1.9GB)
- `.venv/` (257MB)
- `.git/`
