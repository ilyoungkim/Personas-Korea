"""Persona MCP Server — ChatGPT가 한국 페르소나 데이터를 질의하기 위한 MCP 서버.

4개 툴:
    - search_persona    : 구조화 조건 검색
    - aggregate_persona : 집단 통계
    - similar_persona   : 자연어 유사 검색 (Qdrant/LIKE)
    - compare_persona   : 두 집단 비교
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from db.postgres import PersonaDB
from db.qdrant import SimilarityDB

mcp = FastMCP("persona-mcp", host="0.0.0.0", port=19000)

db = PersonaDB()
sim = SimilarityDB()

FILTER_KEYS = {
    "age", "sex", "province", "district", "occupation", "family_type",
    "marital_status", "housing_type", "education_level", "country",
}


def _build_where(filters: dict, age_min: int | None = None, age_max: int | None = None) -> tuple[list[str], list[Any]]:
    """필터 dict → (WHERE 절 리스트, 파라미터 리스트).

    filters: {컬럼명: 값} 또는 {컬럼명: (연산자, 값)}.
    age_min/age_max는 별도 파라미터로 받아 range 조건으로 변환.
    """
    where: list[str] = []
    params: list[Any] = []

    for k, v in filters.items():
        if k not in FILTER_KEYS or v is None or v == "":
            continue
        if isinstance(v, tuple):
            where.append(f"{k} {v[0]} %s")
            params.append(v[1])
        else:
            where.append(f"{k} = %s")
            params.append(v)

    if age_min is not None:
        where.append("age >= %s")
        params.append(age_min)
    if age_max is not None:
        where.append("age <= %s")
        params.append(age_max)

    return where, params


def _parse_filters(raw: dict | None) -> dict:
    if not raw:
        return {}
    return {k: v for k, v in raw.items() if k in FILTER_KEYS and v is not None}


@mcp.tool()
def search_persona(
    age_min: int | None = None,
    age_max: int | None = None,
    sex: str | None = None,
    province: str | None = None,
    district: str | None = None,
    occupation: str | None = None,
    family_type: str | None = None,
    marital_status: str | None = None,
    housing_type: str | None = None,
    education_level: str | None = None,
    limit: int = 20,
) -> dict:
    """구조화된 조건으로 페르소나를 검색합니다. (PostgreSQL)"""
    filters = _parse_filters({
        "sex": sex, "province": province, "district": district,
        "occupation": occupation, "family_type": family_type,
        "marital_status": marital_status, "housing_type": housing_type,
        "education_level": education_level,
    })
    where, params = _build_where(filters, age_min, age_max)
    rows = db.search_raw(where, params, limit)
    return {"count": len(rows), "results": rows}


@mcp.tool()
def aggregate_persona(
    sex: str | None = None,
    age_min: int | None = None,
    age_max: int | None = None,
    province: str | None = None,
    occupation: str | None = None,
    family_type: str | None = None,
) -> dict:
    """필터 조건에 맞는 집단의 인구통계 분포를 반환합니다."""
    filters = _parse_filters({
        "sex": sex, "province": province, "occupation": occupation,
        "family_type": family_type,
    })
    where, params = _build_where(filters, age_min, age_max)
    return db.aggregate_raw(where, params)


@mcp.tool()
def similar_persona(
    query: str,
    limit: int = 10,
    sex: str | None = None,
    province: str | None = None,
    district: str | None = None,
    occupation: str | None = None,
    family_type: str | None = None,
) -> dict:
    """자연어 설명 + 구조화 조건으로 유사한 페르소나를 하이브리드 검색합니다.

    의미 검색(Qdrant 벡터)과 조건 필터(성별/지역/직업/가구)를 결합합니다.
    """
    filters = _parse_filters({
        "sex": sex, "province": province, "district": district,
        "occupation": occupation, "family_type": family_type,
    })
    return sim.similar(query, limit, filters or None)


@mcp.tool()
def cluster_summary(limit: int = 20) -> dict:
    """인구 상위 Core Persona 클러스터 목록을 반환합니다.

    각 클러스터는 연령·성별·지역·가구·직업군으로 세분화된 집단이며,
    자연어 라벨(label)과 인구(population)를 포함합니다.
    """
    clusters = db.list_clusters(limit)
    return {"total_clusters": 924, "top_clusters": clusters}


@mcp.tool()
def cluster_detail(cluster_id: str) -> dict:
    """특정 클러스터의 상세 정보와 대표 페르소나 샘플을 반환합니다."""
    return db.get_cluster(cluster_id)


@mcp.tool()
def core_persona_summary() -> dict:
    """최상위 Core Persona (12개 집단) 요약을 반환합니다.

    전체 인구를 지역(수도권/비수도권) × 직업군 6종으로 압축한 핵심 페르소나입니다.
    예: "수도권 관리자·전문가" (7.1%).
    """
    cores = db.list_core_personas()
    return {"total_core_personas": len(cores), "core_personas": cores}


@mcp.tool()
def core_persona_detail(core_id: str) -> dict:
    """특정 Core Persona의 상세(하위 Major 분해 + 대표 샘플)를 반환합니다."""
    return db.get_core_persona(core_id)


@mcp.tool()
def compare_persona(
    group_a: dict,
    group_b: dict,
) -> dict:
    """두 집단을 구조화 조건으로 비교합니다.

    group_a / group_b는 다음 키를 가질 수 있는 dict입니다:
      sex, province, district, occupation, family_type, marital_status,
      housing_type, education_level, age_min, age_max, label

    예:
      group_a={"label":"서울 30대 여성 1인가구","sex":"여자","province":"서울",
               "age_min":30,"age_max":39,"family_type":"혼자 거주"}
      group_b={"label":"경기 40대 여성 자녀가구","sex":"여자","province":"경기",
               "age_min":40,"age_max":49,"family_type":"배우자·자녀와 거주"}

    결과: 각 집단의 인구·직업·가구·주거·학력·혼인 분포와 상위 직업 차이를 반환합니다.
    """

    def _agg(g: dict) -> dict:
        filters = _parse_filters({
            "sex": g.get("sex"),
            "province": g.get("province"),
            "district": g.get("district"),
            "occupation": g.get("occupation"),
            "family_type": g.get("family_type"),
            "marital_status": g.get("marital_status"),
            "housing_type": g.get("housing_type"),
            "education_level": g.get("education_level"),
        })
        where, params = _build_where(
            filters,
            g.get("age_min"),
            g.get("age_max"),
        )
        return db.aggregate_raw(where, params)

    agg_a = _agg(group_a)
    agg_b = _agg(group_b)

    pop_a = agg_a["population"]
    pop_b = agg_b["population"]
    total = pop_a + pop_b

    # --- 헬퍼: 두 분포 dict의 차이 축약 ---
    def _ratio_map(items: list[dict]) -> dict:
        return {i["key"]: i["ratio"] for i in items}

    def _diff_summary(items_a: list[dict], items_b: list[dict], top_n: int = 5) -> list[dict]:
        """두 분포에서 |비중 차이|가 큰 항목만 top_n개 추출."""
        ma = _ratio_map(items_a)
        mb = _ratio_map(items_b)
        diffs = []
        for key in set(ma) | set(mb):
            ra = ma.get(key, 0.0)
            rb = mb.get(key, 0.0)
            d = ra - rb
            if abs(d) > 0.005:  # 0.5%p 이상 차이만
                diffs.append({
                    "key": key,
                    "group_a_ratio": round(ra, 4),
                    "group_b_ratio": round(rb, 4),
                    "diff": round(d, 4),
                })
        diffs.sort(key=lambda x: -abs(x["diff"]))
        return diffs[:top_n]

    # 상위 항목 요약 (각 분포에서 상위 3개)
    def _top_keys(items: list[dict], n: int = 3) -> list[dict]:
        return items[:n]

    return {
        "group_a": {
            "label": group_a.get("label", "그룹 A"),
            "population": pop_a,
            "population_ratio": round(pop_a / total, 4) if total else 0.0,
        },
        "group_b": {
            "label": group_b.get("label", "그룹 B"),
            "population": pop_b,
            "population_ratio": round(pop_b / total, 4) if total else 0.0,
        },
        "comparison": {
            "population_a": pop_a,
            "population_b": pop_b,
            "population_ratio": round(pop_a / total, 4) if total else 0.0,
            # 유의미한 차이만 축약
            "occupation_diff": _diff_summary(agg_a["occupation"], agg_b["occupation"]),
            "family_type_diff": _diff_summary(agg_a["family_type"], agg_b["family_type"]),
            "housing_type_diff": _diff_summary(agg_a["housing_type"], agg_b["housing_type"]),
            "education_diff": _diff_summary(agg_a["education_level"], agg_b["education_level"]),
            # 각 그룹의 대표 상위 항목
            "top_occupation_a": _top_keys(agg_a["occupation"]),
            "top_occupation_b": _top_keys(agg_b["occupation"]),
        },
    }


def main() -> None:
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--http":
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
