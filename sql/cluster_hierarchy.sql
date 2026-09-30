-- ============================================================
-- ④ Clustering 계층화
-- 924 Micro → Major(≈24) → Core(≈12)
--
-- Micro: age_group × sex × region_group × family_group × occupation_group
-- Major: sex × region_group × occupation_group
-- Core : region_group × occupation_group
-- ============================================================

-- ---------- Major Cluster ----------
DROP TABLE IF EXISTS major_cluster;
CREATE TABLE major_cluster AS
SELECT
  'M' || lpad(CAST(row_number() OVER (ORDER BY count(*) DESC) AS text), 2, '0') AS major_id,
  sex,
  region_group,
  occupation_group,
  count(*) AS population,
  round(count(*)::numeric / 1000000, 6) AS population_ratio
FROM persona_cluster
GROUP BY 2, 3, 4;

ALTER TABLE major_cluster ADD COLUMN IF NOT EXISTS label TEXT;
UPDATE major_cluster
SET label = region_group || ' ' || occupation_group || ' ' || sex;

CREATE INDEX IF NOT EXISTS idx_major_id ON major_cluster(major_id);

-- ---------- Core Persona ----------
DROP TABLE IF EXISTS core_persona;
CREATE TABLE core_persona AS
SELECT
  'P' || lpad(CAST(row_number() OVER (ORDER BY count(*) DESC) AS text), 2, '0') AS core_id,
  region_group,
  occupation_group,
  count(*) AS population,
  round(count(*)::numeric / 1000000, 6) AS population_ratio
FROM persona_cluster
GROUP BY 2, 3;

ALTER TABLE core_persona ADD COLUMN IF NOT EXISTS label TEXT;
UPDATE core_persona
SET label = region_group || ' ' || occupation_group;

CREATE INDEX IF NOT EXISTS idx_core_id ON core_persona(core_id);

-- 결과 확인
SELECT 'MAJOR' AS level, count(*) AS cnt FROM major_cluster
UNION ALL SELECT 'CORE', count(*) FROM core_persona;
