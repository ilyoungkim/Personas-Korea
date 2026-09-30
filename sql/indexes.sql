-- 검색 최적화용 인덱스
-- 자주 필터링되는 컬럼에 대해 B-tree 인덱스 생성

CREATE INDEX IF NOT EXISTS idx_persona_age          ON persona(age);
CREATE INDEX IF NOT EXISTS idx_persona_sex          ON persona(sex);
CREATE INDEX IF NOT EXISTS idx_persona_province     ON persona(province);
CREATE INDEX IF NOT EXISTS idx_persona_district     ON persona(district);
CREATE INDEX IF NOT EXISTS idx_persona_occupation   ON persona(occupation);
CREATE INDEX IF NOT EXISTS idx_persona_family_type  ON persona(family_type);
CREATE INDEX IF NOT EXISTS idx_persona_marital      ON persona(marital_status);
CREATE INDEX IF NOT EXISTS idx_persona_housing      ON persona(housing_type);
CREATE INDEX IF NOT EXISTS idx_persona_education    ON persona(education_level);

-- 복합 인덱스 (대표 검색 패턴)
CREATE INDEX IF NOT EXISTS idx_persona_age_gender    ON persona(age, sex);
CREATE INDEX IF NOT EXISTS idx_persona_prov_district ON persona(province, district);
CREATE INDEX IF NOT EXISTS idx_persona_age_sex_prov  ON persona(age, sex, province);
