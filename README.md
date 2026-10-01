# Korea Persona Intelligence

100만 한국 합성 페르소나 데이터(`nvidia/Nemotron-Personas-Korea`)를
PostgreSQL + Qdrant + MCP + Nuxt 대시보드로 서비스하고, ChatGPT(및 MCP 지원
클라이언트)가 한국 페르소나에게 "질문"할 수 있게 하는 로컬(192.168.x.x) 전용 시스템.

> 전체 개발 계획 및 로드맵은 [plan.md](plan.md) 참조.

---

## 아키텍처

```
ChatGPT ──MCP──▶ persona-mcp ──┬─ PostgreSQL (조건/통계/클러스터)
                               └─ Qdrant (의미 검색)
```

| 서비스 | 역할 | 포트 |
|---|---|---|
| postgres | 100만 페르소나 저장/검색/집계 | 15432 |
| qdrant | 벡터 의미 검색 (10K POC) | 16333/16334 |
| mcp | MCP 서버 (4 tools) | 19000 |
| dashboard | Nuxt 대시보드 | 18080 |
| etl | parquet → PostgreSQL 적재 (일회성) | — |
| embed | 임베딩 → Qdrant (일회성) | — |

---

## 빠른 시작

```bash
# 1) 전체 기동 (postgres, qdrant, mcp, dashboard)
docker compose up -d

# 2) 데이터 적재 (최초 1회, 100만 건)
docker compose run --rm etl

# 3) 임베딩 POC (10,000건 → Qdrant)
docker compose run --rm embed
```

### 접속

| 서비스 | URL |
|---|---|
| 대시보드 | http://192.168.31.253:18080 |
| MCP Server | http://192.168.31.253:19000/mcp |
| PostgreSQL | postgresql://persona:persona@192.168.31.253:15432/persona |
| Qdrant | http://192.168.31.253:16333 |

---

## MCP 도구 (8개)

| Tool | 설명 | 데이터 소스 |
|---|---|---|
| `search_persona` | 구조화 조건 검색 (연령/성별/지역/직업 등) | PostgreSQL |
| `aggregate_persona` | 집단 통계 (인구/분포/상위 직업) | PostgreSQL |
| `similar_persona` | 하이브리드 의미+조건 검색 | Qdrant (LIKE 폴백) |
| `compare_persona` | 두 집단 비교 (유의미한 차이 축약) | PostgreSQL |
| `cluster_summary` | Micro 클러스터 목록 (924개) | PostgreSQL |
| `cluster_detail` | 클러스터 상세 + 대표 샘플 | PostgreSQL |
| `core_persona_summary` | Core Persona 요약 (12개, LLM 별칭 포함) | PostgreSQL |
| `core_persona_detail` | Core 상세 + 하위 Major 분해 | PostgreSQL |

---

## ChatGPT 연결

### 방법 A — 원격 URL (streamable-http)

MCP 지원 클라이언트에 다음 URL을 등록:

```
http://192.168.31.253:19000/mcp
```

또는 `mcp-config.json` (프로젝트 루트) 내용을 클라이언트 설정에 복사.

### 방법 B — stdio (로컬)

```json
{
  "mcpServers": {
    "persona": {
      "command": "docker",
      "args": ["exec", "-i", "persona-mcp", "python", "server.py"]
    }
  }
}
```

---

## 예시 질문

ChatGPT에서 연결 후 이런 질문이 동작합니다:

- "한국 40대 여성 중 경기도 거주자는 몇 명이고 주요 직업은?"
- "서울 30대 1인가구와 경기 40대 자녀가구를 비교해줘"
- "자녀 교육과 건강관리에 관심이 많은 수도권 40대 여성 페르소나를 찾아줘"

---

## API 호출 매뉴얼

### 1. 대시보드 REST API

대시보드 자체 API (PostgreSQL 직접 접근). 기본 주소 `http://192.168.31.253:18080`

| Method | 경로 | 설명 |
|---|---|---|
| GET | `/api/stats` | 전체 통계 (총 인구, 지역/성별/연령 분포) |
| GET | `/api/search` | 구조화 조건 검색 |
| GET | `/api/similar` | 키워드 의미 검색 (LIKE 기반) |
| GET | `/api/mcp/tools` | MCP 툴 목록 조회 (MCP 경유) |
| POST | `/api/mcp/call` | MCP 툴 실행 (MCP 경유) |

**예시:**

```bash
# 전체 통계
curl http://192.168.31.253:18080/api/stats

# 구조화 검색 (경기 40대 여성)
curl 'http://192.168.31.253:18080/api/search?province=경기&age_min=40&age_max=49&sex=여자&limit=5'

# 의미 검색
curl 'http://192.168.31.253:18080/api/similar?q=자녀%20교육'

# MCP 툴 목록
curl http://192.168.31.253:18080/api/mcp/tools

# MCP 툴 실행 (집단 통계)
curl -X POST http://192.168.31.253:18080/api/mcp/call \
  -H 'Content-Type: application/json' \
  -d '{"toolName":"aggregate_persona","args":{"province":"경기","sex":"여자"}}'
```

### 2. MCP 서버 직접 호출 (streamable-http)

MCP 프로토콜 원격 호출. 주소 `http://192.168.31.253:19000/mcp`

```bash
# initialize (세션 획득)
curl -X POST http://192.168.31.253:19000/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
```

> MCP는 세션 기반이므로, `initialize` 응답 헤더의 `Mcp-Session-Id`를 이후 요청에 포함해야 합니다.
> 실제 클라이언트 연결은 `mcp-config.json` 또는 ChatGPT의 원격 URL 등록을 권장합니다.

### 3. Python 클라이언트 예시

```python
import asyncio, json
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

async def main():
    async with streamablehttp_client('http://192.168.31.253:19000/mcp') as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool('similar_persona', arguments={
                'query': '자녀 교육에 관심이 많은 40대 여성',
                'province': '경기',
                'limit': 5,
            })
            print(json.loads(res.content[0].text))

asyncio.run(main())
```

---

## 종료

```bash
docker compose down        # 컨테이너만
docker compose down -v     # 볼륨(데이터)까지 삭제
```

---

## 라이선스

### 데이터셋

본 프로젝트가 사용하는 `nvidia/Nemotron-Personas-Korea` 데이터셋은
[크리에이티브 커먼즈 저작자표시 4.0 국제 라이선스 (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)에 따라 제공됩니다.
상업적·비상업적 용도 모두 자유롭게 사용할 수 있으나, **저작자 표시(Attribution)**가 필요합니다.

- 데이터셋: [nvidia/Nemotron-Personas-Korea](https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea)
- 라이선스: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- 저작자: NVIDIA Corporation

```bibtex
@software{nvidia/Nemotron-Personas-Korea,
  author = {Kim, Hyunwoo and Ryu, Jihyeon and Lee, Jinho and Ryu, Hyungon and Praveen, Kiran and Prayaga, Shyamala and Thadaka, Kirit and Jennings, Will and Sadeghi, Bardiya and Sharabiani, Ashton and Choi, Yejin and Meyer, Yev},
  title = {Nemotron-Personas-Korea: Synthetic Personas Aligned to Real-World Distributions for Korea},
  month = {April},
  year = {2026},
  url = {https://huggingface.co/datasets/nvidia/Nemotron-Personas-Korea}
}
```

### 프로그램 (코드)

본 프로젝트의 소스 코드는 [Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0)에 따라 배포됩니다.
전체 내용은 [LICENSE](LICENSE) 파일을 참조하세요.
