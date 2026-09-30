# Korea Persona Intelligence — 개발 계획서

> 100만 한국 합성 페르소나 데이터를 PostgreSQL + Qdrant + MCP + Nuxt 대시보드로
> 서비스하고, ChatGPT(및 MCP 지원 클라이언트)가 한국 페르소나에게 "질문"할 수 있게
> 하는 로컬(192.168.x.x) 전용 시스템.

---

## 1. 목표 (Goals)

- **1차 목표**: `PostgreSQL + Qdrant + MCP + Nuxt Dashboard` 4개를 Docker로 완성하고,
  ChatGPT에서 "한국 페르소나에게 질문한다"는 경험을 만든다.
- 데이터 계층과 AI 호출 계층을 **분리**하여 단계적으로 확장한다.
- 100만 건을 한 번에 AI에 던지지 않고, **통계·집계로 축약**해 전달한다.

---

## 2. 최종 아키텍처

```
                        ┌──────────────────┐
                        │     ChatGPT      │
                        └────────┬─────────┘
                                 │  MCP Protocol
                        ┌────────▼─────────┐
                        │ Persona MCP      │
                        │ Server           │
                        └────────┬─────────┘
                    ┌─────────────┼─────────────┐
                    ▼             ▼             ▼
              PostgreSQL       Qdrant       Analytics
              1M Persona      Vector DB       Engine
```

Docker Compose 구성:

```
persona-mcp      (Python MCP Server, streamable-http)
postgres         (100만 페르소나, 사실/통계)
qdrant           (의미 검색용 벡터 저장소 — 확장 예정)
dashboard        (Nuxt.js 대시보드)
etl              (일회성: parquet → PostgreSQL 적재)
```

> Redis, Kafka, Kubernetes는 1차 범위에서 제외한다.

---

## 3. 데이터 소스

| 항목 | 값 |
|---|---|
| 데이터셋 | `nvidia/Nemotron-Personas-Korea` |
| 라이선스 | CC BY 4.0 |
| 규모 | 100만 레코드 / 700만 페르소나 문장 / 1.7B 토큰 |
| 포맷 | Parquet (9개 샤드, 각 210MB) |
| 필드 | 26개 (식별자 1 + 페르소나 7 + 속성 6 + 인구통계·지리 12) |

### 26개 필드

- **식별자**: `uuid`
- **페르소나 (7)**: `persona`, `professional_persona`, `sports_persona`,
  `arts_persona`, `travel_persona`, `culinary_persona`, `family_persona`
- **속성 (6)**: `cultural_background`, `skills_and_expertise`,
  `skills_and_expertise_list`, `hobbies_and_interests`,
  `hobbies_and_interests_list`, `career_goals_and_ambitions`
- **인구통계·지리 (12)**: `sex`, `age`, `marital_status`, `military_status`,
  `family_type`, `housing_type`, `education_level`, `bachelors_field`,
  `occupation`, `district`, `province`, `country`

> 원본에 없는 필드(소득 `income_level`, 자녀 `children`)는 **스키마에 억지로 만들지
> 않고**, 존재하는 필드만 그대로 보존한다(Raw 데이터 보존 원칙).

---

## 4. 데이터 스키마 (PostgreSQL)

### `persona` — Raw 보존 테이블

원본 26개 필드를 모두 컬럼으로 보존 (`uuid` TEXT PK + 25개 필드 + `created_at`).

### `region` — 지역 코드 테이블

```sql
code        TEXT PRIMARY KEY
province    TEXT   -- 시도
district    TEXT   -- 시군구
region_type TEXT   -- 지역유형(수도권/지방, 추후 분류)
```

### 인덱스

- 단일: `age`, `sex`, `province`, `district`, `occupation`, `family_type`,
  `marital_status`, `housing_type`, `education_level`
- 복합: `(age, sex)`, `(province, district)`, `(age, sex, province)`

---

## 5. MCP Tools (4개)

| Tool | 설명 | 데이터 소스 |
|---|---|---|
| `search_persona` | 구조화 조건 검색 (연령/성별/지역/직업 등) | PostgreSQL |
| `aggregate_persona` | 집단 통계 (인구/분포/상위 관심사) | PostgreSQL |
| `similar_persona` | 자연어 의미 검색 | Qdrant (POC: LIKE 폴백) |
| `compare_persona` | 두 집단 비교 | PostgreSQL |

### "작게 반환" 원칙

MCP는 원본 페르소나를 통째로 반환하지 않고, **집계·통계로 축약한 50~100개 핵심
데이터**만 반환한다. 그래야 ChatGPT가 정확히 해석할 수 있다.

---

## 6. 포트 배정 (기존 포트 회피)

| 서비스 | 호스트 포트 | 컨테이너 포트 |
|---|---|---|
| PostgreSQL | `15432` | 5432 |
| Qdrant HTTP | `16333` | 6333 |
| Qdrant gRPC | `16334` | 6334 |
| MCP Server | `19000` | 19000 |
| Nuxt Dashboard | `18080` | 18080 |

> 회피한 기존 포트: 5432, 8080, 5000, 7000, 8443, 8444, 11434 등.
> 모든 서비스는 `0.0.0.0` 바인딩으로 **로컬 192.168.x.x 대역에서 접근 가능**.

---

## 7. 프로젝트 구조

```
Personas-Korea/
├── docker-compose.yml
├── plan.md
├── sql/
│   ├── schema.sql
│   └── indexes.sql
├── etl/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── load_data.py          # parquet → PostgreSQL
├── mcp/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── server.py             # FastMCP 서버 (4 tools)
│   └── db/
│       ├── postgres.py       # PersonaDB
│       └── qdrant.py         # SimilarityDB
├── dashboard/
│   ├── Dockerfile
│   ├── nuxt.config.ts
│   ├── package.json
│   ├── app.vue
│   ├── components/BarCard.vue
│   └── server/api/
│       ├── stats.get.ts
│       └── search.get.ts
├── data/
│   ├── parquet/              # 원본 parquet (ETL 입력)
│   └── nemotron_personas_korea.csv   # CSV 추출본 (4.1GB)
├── download_dataset.py       # HF Hub → parquet/CSV
├── main.py
└── pyproject.toml
```

---

## 8. 개발 단계 및 현재 상태

| 단계 | 작업 | 결과 |
|---|---|---|
| 0 | 원본 데이터 분석 | ✅ 스키마 26필드 확정 |
| 1 | PostgreSQL 구축 | ✅ 스키마/인덱스 |
| 2 | 100만 Persona 적재 | ✅ 1,000,000행 (616초) |
| 3 | Index/Query | ✅ 조건 검색 동작 |
| 4 | Aggregation | ✅ 집단 통계 동작 |
| 5 | Clustering | ⏳ 예정 |
| 6 | Embedding | ⏳ 예정 |
| 7 | Qdrant 의미 검색 | 🟡 POC(LIKE 폴백) |
| 8 | Hybrid Search | ⏳ 예정 |
| 9 | MCP 4개 Tool | ✅ 구현·기동 |
| 10 | Docker 전체 컨테이너화 | ✅ 완료 |
| 11 | ChatGPT 연결 | ⏳ 클라이언트 연결 대기 |
| 12 | 성능 테스트 | ⏳ 예정 |

---

## 9. 배포 및 운영

### 기동

```bash
# 전체 서비스
docker compose up -d

# 데이터 재적재 (필요 시)
docker compose run --rm etl
```

### 접속

| 서비스 | URL |
|---|---|
| 대시보드 | `http://192.168.31.253:18080` |
| MCP Server | `http://192.168.31.253:19000/mcp` |
| PostgreSQL | `postgresql://persona:persona@192.168.31.253:15432/persona` |
| Qdrant | `http://192.168.31.253:16333` |

### 종료

```bash
docker compose down            # 컨테이너만
docker compose down -v         # 볼륨(데이터)까지 삭제
```

---

## 10. 검증 결과 (2026-09-30)

| 항목 | 결과 |
|---|---|
| PostgreSQL 적재 | ✅ 1,000,000 행 |
| region 테이블 | ✅ 252 건 (시군구) |
| 대시보드 `/api/stats` | ✅ `total: 1000000` |
| 대시보드 `/api/search` | ✅ 조건 검색 정상 |
| MCP `initialize` 핸드셰이크 | ✅ `persona-mcp` v1.30.0 |
| LAN 접근 (192.168.31.253) | ✅ 정상 |

---

## 11. 다음 단계 (로드맵)

1. **Clustering**: 통계 조건(연령+지역+성별+가구+직업) 기반 1차 그룹 → 100~300
   Micro Cluster → 20~50 Major → 10~20 Core Persona (이름은 LLM 생성).
2. **Embedding + Qdrant**: 페르소나 텍스트 임베딩 → 벡터 검색 활성화.
   POC 규모 10,000 → 100,000 → 1,000,000 순서로 확대.
3. **Hybrid Search**: RDB(조건) + Vector(의미) 결합.
4. **ChatGPT 연결**: MCP 클라이언트 설정으로 실제 대화 테스트.
5. **성능 테스트**: 100만 건 쿼리 지연/처리량 검증.
