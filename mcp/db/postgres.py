"""Persona 데이터 접근 계층 — PostgreSQL + Qdrant."""

from __future__ import annotations

import os
from typing import Any

import psycopg
from psycopg.rows import dict_row

PG_DSN = os.getenv("PG_DSN", "postgresql://persona:persona@postgres:5432/persona")


class PersonaDB:
    def __init__(self, dsn: str = PG_DSN):
        self.dsn = dsn

    def _conn(self):
        return psycopg.connect(self.dsn, row_factory=dict_row)

    def count(self) -> int:
        with self._conn() as conn:
            return conn.execute("SELECT count(*) AS n FROM persona").fetchone()["n"]

    def search(self, filters: dict[str, Any], limit: int = 20) -> list[dict]:
        """구조화 조건 검색. 필터 키는 컬럼명, 값은 (연산자, 값) 또는 단일 값."""
        where: list[str] = []
        params: list[Any] = []
        for col, val in filters.items():
            if val is None:
                continue
            if isinstance(val, tuple):
                op, v = val
            else:
                op, v = "=", val
            op = op.upper()
            where.append(f"{col} {op} %s")
            params.append(v)
        q = "SELECT * FROM persona"
        if where:
            q += " WHERE " + " AND ".join(where)
        q += f" LIMIT {int(limit)}"
        with self._conn() as conn:
            return conn.execute(q, params).fetchall()

    def aggregate(self, filters: dict[str, Any], group_by: str | None = None) -> dict:
        """집단 통계. 필터에 맞는 인구 분포를 반환."""
        where: list[str] = []
        params: list[Any] = []
        for col, val in filters.items():
            if val is None:
                continue
            if isinstance(val, tuple):
                op, v = val
            else:
                op, v = "=", val
            where.append(f"{col} {op.upper()} %s")
            params.append(v)
        cond = (" WHERE " + " AND ".join(where)) if where else ""

        with self._conn() as conn:
            total = conn.execute(f"SELECT count(*) AS n FROM persona{cond}", params).fetchone()["n"]

            def dist(expr: str, order: str = "cnt DESC") -> list[dict]:
                rows = conn.execute(
                    f"SELECT {expr} AS key, count(*) AS cnt "
                    f"FROM persona{cond} GROUP BY {expr} ORDER BY {order} LIMIT 20",
                    params,
                ).fetchall()
                return [{"key": r["key"], "count": r["cnt"],
                         "ratio": round(r["cnt"] / total, 4) if total else 0.0} for r in rows]

            result = {
                "population": total,
                "sex": dist("sex"),
                "age": dist("CASE WHEN age<20 THEN '10대' WHEN age<30 THEN '20대' WHEN age<40 THEN '30대' WHEN age<50 THEN '40대' WHEN age<60 THEN '50대' WHEN age<70 THEN '60대' ELSE '70대이상' END"),
                "province": dist("province"),
                "occupation": dist("occupation"),
                "family_type": dist("family_type"),
                "housing_type": dist("housing_type"),
                "marital_status": dist("marital_status"),
                "education_level": dist("education_level"),
                "hobbies": dist("hobbies_and_interests_list"),
            }
            if group_by:
                result["group_by"] = group_by
            return result

    def search_raw(self, where: list[str], params: list[Any], limit: int = 20) -> list[dict]:
        q = "SELECT uuid, sex, age, province, district, occupation, family_type, housing_type, marital_status, education_level, persona FROM persona"
        if where:
            q += " WHERE " + " AND ".join(where)
        q += f" LIMIT {int(limit)}"
        with self._conn() as conn:
            return conn.execute(q, params).fetchall()

    def aggregate_raw(self, where: list[str], params: list[Any]) -> dict:
        cond = (" WHERE " + " AND ".join(where)) if where else ""
        with self._conn() as conn:
            total = conn.execute(f"SELECT count(*) AS n FROM persona{cond}", params).fetchone()["n"]

            def dist(expr: str) -> list[dict]:
                rows = conn.execute(
                    f"SELECT {expr} AS key, count(*) AS cnt "
                    f"FROM persona{cond} GROUP BY {expr} ORDER BY cnt DESC LIMIT 20",
                    params,
                ).fetchall()
                return [{"key": r["key"], "count": r["cnt"],
                         "ratio": round(r["cnt"] / total, 4) if total else 0.0} for r in rows]

            return {
                "population": total,
                "sex": dist("sex"),
                "age": dist("CASE WHEN age<20 THEN '10대' WHEN age<30 THEN '20대' WHEN age<40 THEN '30대' WHEN age<50 THEN '40대' WHEN age<60 THEN '50대' WHEN age<70 THEN '60대' ELSE '70대이상' END"),
                "province": dist("province"),
                "occupation": dist("occupation"),
                "family_type": dist("family_type"),
                "housing_type": dist("housing_type"),
                "marital_status": dist("marital_status"),
                "education_level": dist("education_level"),
            }

    def compare(self, a: dict, b: dict) -> dict:
        return {"group_a": self.aggregate(a), "group_b": self.aggregate(b)}

    def list_core_personas(self) -> list[dict]:
        """Core Persona (최상위 12개 집단) 목록 반환."""
        with self._conn() as conn:
            return conn.execute(
                "SELECT core_id, label, alias, population, population_ratio "
                "FROM core_persona ORDER BY population DESC"
            ).fetchall()

    def list_major_clusters(self, limit: int = 24) -> list[dict]:
        """Major Cluster (중간 계층) 목록 반환."""
        with self._conn() as conn:
            return conn.execute(
                "SELECT major_id, label, sex, region_group, occupation_group, "
                "population, population_ratio "
                "FROM major_cluster ORDER BY population DESC LIMIT %s",
                (limit,),
            ).fetchall()

    def get_core_persona(self, core_id: str) -> dict:
        """특정 Core Persona의 상세 + 하위 Major 분해 + 대표 샘플 반환."""
        with self._conn() as conn:
            info = conn.execute(
                "SELECT core_id, label, alias, population, population_ratio "
                "FROM core_persona WHERE core_id = %s",
                (core_id,),
            ).fetchone()
            if info is None:
                return {"error": f"core persona {core_id} not found"}

            # 하위 Major 클러스터 분해
            region_group = info["label"].split(" ")[0]
            occupation_group = info["label"].split(" ", 1)[1]
            majors = conn.execute(
                "SELECT major_id, label, sex, population, population_ratio "
                "FROM major_cluster WHERE region_group = %s AND occupation_group = %s "
                "ORDER BY population DESC",
                (region_group, occupation_group),
            ).fetchall()

            # 대표 샘플 3건
            samples = conn.execute(
                "SELECT p.uuid, p.sex, p.age, p.province, p.district, p.occupation, p.persona "
                "FROM persona_cluster pc "
                "JOIN persona p ON p.uuid = pc.uuid "
                "WHERE pc.region_group = %s AND pc.occupation_group = %s "
                "LIMIT 3",
                (region_group, occupation_group),
            ).fetchall()

            return {"core": info, "major_breakdown": majors, "samples": samples}

    def list_clusters(self, limit: int = 20) -> list[dict]:
        """인구 상위 클러스터 목록 (Core Persona) 반환."""
        with self._conn() as conn:
            return conn.execute(
                "SELECT cluster_id, label, age_group, sex, region_group, "
                "family_group, occupation_group, population, population_ratio "
                "FROM cluster_stats ORDER BY population DESC LIMIT %s",
                (limit,),
            ).fetchall()

    def get_cluster(self, cluster_id: str) -> dict:
        """특정 클러스터의 상세 정보 + 대표 페르소나 샘플 반환."""
        with self._conn() as conn:
            info = conn.execute(
                "SELECT cluster_id, label, age_group, sex, region_group, "
                "family_group, occupation_group, population, population_ratio "
                "FROM cluster_stats WHERE cluster_id = %s",
                (cluster_id,),
            ).fetchone()
            if info is None:
                return {"error": f"cluster {cluster_id} not found"}

            # persona_cluster 테이블의 같은 축 조합에 속하는 샘플 5건
            samples = conn.execute(
                "SELECT pc.uuid, p.sex, p.age, p.province, p.district, "
                "p.occupation, p.family_type, p.persona "
                "FROM persona_cluster pc "
                "JOIN persona p ON p.uuid = pc.uuid "
                "WHERE pc.age_group = %s AND pc.sex = %s "
                "AND pc.region_group = %s AND pc.family_group = %s "
                "AND pc.occupation_group = %s "
                "LIMIT 5",
                (info["age_group"], info["sex"], info["region_group"],
                 info["family_group"], info["occupation_group"]),
            ).fetchall()

            return {"cluster": info, "samples": samples}
