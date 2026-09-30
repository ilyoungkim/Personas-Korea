"""⑦ 기능 검증 + 클래스별 질문 정확성 확인 (가벼운 벤치).

목적:
  1. 4개 MCP 툴이 정상 응답하는지 (지연시간 포함, 3회 평균)
  2. 100만 건 데이터에 대한 클래스(클러스터/페르소나 유형)별 질문이
     정확하게 나오는지 확인

동시 사용자 3명 수준의 가벼운 검증이므로 스트레스 테스트는 하지 않습니다.
"""

import asyncio
import json
import time

import psycopg
from psycopg.rows import dict_row
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

URL = "http://192.168.31.253:19000/mcp"
PG_DSN = "postgresql://persona:persona@192.168.31.253:15432/persona"
N_RUNS = 3


async def bench_tool(session, name, args):
    """툴을 N_RUNS번 호출해 평균 지연시간과 정상 여부를 반환."""
    latencies = []
    result = None
    for _ in range(N_RUNS):
        t0 = time.perf_counter()
        res = await session.call_tool(name, arguments=args)
        latencies.append(time.perf_counter() - t0)
        try:
            result = json.loads(res.content[0].text)
        except Exception:
            result = {"raw": res.content[0].text if res.content else ""}
    avg = sum(latencies) / len(latencies)
    return avg, result


async def main():
    print("=" * 60)
    print("⑦ 기능 검증 + 클래스별 질문 정확성")
    print("=" * 60)

    async with streamablehttp_client(URL) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()

            cases = [
                ("search_persona", {"province": "경기", "age_min": 40, "age_max": 49, "sex": "여자", "limit": 5}),
                ("aggregate_persona", {"province": "경기", "age_min": 40, "age_max": 49, "sex": "여자"}),
                ("similar_persona", {"query": "자녀 교육과 건강관리에 관심이 많은 수도권 40대 맞벌이 여성", "limit": 5}),
                ("compare_persona", {
                    "group_a": {"label": "서울 30대 여성 1인가구", "sex": "여자", "province": "서울", "age_min": 30, "age_max": 39, "family_type": "혼자 거주"},
                    "group_b": {"label": "경기 40대 여성 자녀가구", "sex": "여자", "province": "경기", "age_min": 40, "age_max": 49, "family_type": "배우자·자녀와 거주"},
                }),
            ]

            print("\n[1] MCP 툴 기능 정상 여부 + 지연시간")
            print("-" * 60)
            for name, args in cases:
                avg, result = await bench_tool(s, name, args)
                # 정상 여부 판단
                if "results" in result or "population" in result or "comparison" in result:
                    ok = "OK"
                    detail = ""
                    if "population" in result:
                        detail = f"population={result['population']:,}"
                    elif "results" in result:
                        detail = f"results={len(result['results'])}건"
                    elif "comparison" in result:
                        detail = f"pop_a={result['comparison']['population_a']:,}"
                else:
                    ok = "FAIL"
                    detail = str(result)[:80]
                print(f"  {name:<20} {avg*1000:7.1f}ms  {ok}  {detail}")

    print("\n[2] 클래스(클러스터)별 질문 정확성")
    print("-" * 60)
    with psycopg.connect(PG_DSN, row_factory=dict_row) as conn:
        # 클러스터 총합 검증
        total = conn.execute("SELECT count(*) AS n FROM persona").fetchone()["n"]
        csum = conn.execute("SELECT sum(population) AS s, count(*) AS c FROM cluster_stats").fetchone()
        print(f"  persona 총 행: {total:,}")
        print(f"  클러스터 수:   {csum['c']}")
        print(f"  클러스터 population 합: {csum['s']:,}  (일치 여부: {'OK' if csum['s'] == total else 'FAIL'})")

        # 대표 클러스터 질문 정확성
        print("\n  대표 클러스터 (인구 상위 5):")
        rows = conn.execute(
            "SELECT cluster_id, age_group, sex, region_group, family_group, occupation_group, population "
            "FROM cluster_stats ORDER BY population DESC LIMIT 5"
        ).fetchall()
        for r in rows:
            print(f"    {r['cluster_id']}  {r['age_group']} {r['sex']} {r['region_group']} "
                  f"{r['family_group']} {r['occupation_group']}  → {r['population']:,}명")

        # 특정 클래스 질문: "경기 40대 여성" 클러스터 조회 정확성
        print("\n  질문: '경기 40대 여성' 클러스터는?")
        q = conn.execute(
            "SELECT cluster_id, family_group, occupation_group, population "
            "FROM cluster_stats "
            "WHERE age_group='40대' AND sex='여자' AND region_group='수도권' "
            "ORDER BY population DESC LIMIT 5"
        ).fetchall()
        for r in q:
            print(f"    {r['cluster_id']}  {r['family_group']} {r['occupation_group']}  → {r['population']:,}명")

        # 페르소나 유형(7종)별 존재 여부 확인
        print("\n  페르소나 유형(7종)별 비어있지 않은 레코드 수:")
        for col in ["professional_persona", "sports_persona", "arts_persona",
                    "travel_persona", "culinary_persona", "family_persona", "persona"]:
            n = conn.execute(f"SELECT count(*) AS n FROM persona WHERE {col} IS NOT NULL AND {col} != ''").fetchone()["n"]
            print(f"    {col:<24} {n:,}")

    print("\n" + "=" * 60)
    print("검증 완료")


if __name__ == "__main__":
    asyncio.run(main())
