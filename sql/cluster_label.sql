-- ============================================================
-- ① Core Persona 이름 생성 (규칙 기반)
-- cluster_stats에 자연어 라벨(label) 컬럼 추가
--
-- 예: "수도권 40대 여성 부부+자녀 무직"
-- ============================================================

ALTER TABLE cluster_stats ADD COLUMN IF NOT EXISTS label TEXT;

UPDATE cluster_stats
SET label = region_group || ' ' || age_group || ' ' || sex
            || ' ' || family_group || ' ' || occupation_group;

-- 대표 상위 클러스터 확인
SELECT cluster_id, label, population
FROM cluster_stats
ORDER BY population DESC
LIMIT 15;
