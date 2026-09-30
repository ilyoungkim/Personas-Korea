-- Nemotron-Personas-Korea 스키마
-- 원본 26개 필드를 모두 보존 (버리지 않음)

CREATE TABLE IF NOT EXISTS persona (
    uuid                      TEXT PRIMARY KEY,
    -- 인구통계·지리 컨텍스트 (12)
    sex                       TEXT,
    age                       INTEGER,
    marital_status            TEXT,
    military_status           TEXT,
    family_type               TEXT,
    housing_type              TEXT,
    education_level           TEXT,
    bachelors_field           TEXT,
    occupation                TEXT,
    district                  TEXT,
    province                  TEXT,
    country                   TEXT,
    -- 페르소나 속성 (6)
    cultural_background       TEXT,
    skills_and_expertise      TEXT,
    skills_and_expertise_list TEXT,
    hobbies_and_interests     TEXT,
    hobbies_and_interests_list TEXT,
    career_goals_and_ambitions TEXT,
    -- 페르소나 (7)
    persona                   TEXT,
    professional_persona      TEXT,
    sports_persona            TEXT,
    arts_persona              TEXT,
    travel_persona            TEXT,
    culinary_persona          TEXT,
    family_persona            TEXT,
    created_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 지역 참조 테이블 (시도/시군구/지역코드/지역유형)
CREATE TABLE IF NOT EXISTS region (
    code        TEXT PRIMARY KEY,   -- 시도코드 + 시군구코드
    province    TEXT NOT NULL,      -- 시도
    district    TEXT NOT NULL,      -- 시군구
    region_type TEXT                -- 지역유형 (수도권/지방 등, 추후 분류)
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_region_prov_dist ON region(province, district);
