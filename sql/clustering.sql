-- ============================================================
-- ② Persona Clustering (1차: 통계 기반)
-- 100만 페르소나를 의미있는 축으로 롤업하여 Micro Cluster를 만든다.
--
-- 축:
--   age_group       7개 (10대~70대이상)
--   sex             2개
--   region_group    2개 (수도권/비수도권)
--   family_group    6개 (1인/부부/부부+자녀/한부모/부모동거/다세대)
--   occupation_group 6개 (무직/고숙련/사무/서비스판매/기능단순노무/기타)
--
-- 결과: persona_cluster (개별 할당) + cluster_stats (집계)
-- ============================================================

-- ---------- 1) occupation 대분류 롤업 매핑 테이블 ----------
DROP TABLE IF EXISTS occupation_category;
CREATE TABLE occupation_category AS
SELECT occupation,
       CASE
         WHEN occupation = '무직' THEN '무직'
         WHEN occupation ~ '경영자|관리자|대표|임원|이사' THEN '관리자·전문가'
         WHEN occupation ~ '전문가|교사|교수|의사|간호|약사|변호|연구|설계|개발|프로그래머|엔지니어|기술자|컨설턴트|회계사|세무|공학|의료|물리치료|영양사|심리|사회복지|종교|기자|작가|예술|디자이너|통역|번역' THEN '관리자·전문가'
         WHEN occupation ~ '사무원|사무직|비서|경리|회계|상담원|접수|기획|총무|인사|전산|출납|속기|안내' THEN '사무'
         WHEN occupation ~ '조리|요리|서비스|미용|이용|숙박|여행|승무|경호|보안|판매|판매원|영업원|바리스타|주방|요리사|안내원' THEN '서비스·판매'
         WHEN occupation ~ '기능|정비|수리|용접|배관|전기|전자|운전|조작|조립|제조|설치|목공|도장|건설|채굴|농림|어업|축산' THEN '기능·기계·단순노무'
         ELSE '기타'
       END AS category
FROM (SELECT DISTINCT occupation FROM persona) t;

-- ---------- 2) Micro Cluster 할당 테이블 ----------
DROP TABLE IF EXISTS persona_cluster;
CREATE TABLE persona_cluster AS
SELECT
  uuid,
  -- age_group
  CASE
    WHEN age < 20 THEN '10대'
    WHEN age < 30 THEN '20대'
    WHEN age < 40 THEN '30대'
    WHEN age < 50 THEN '40대'
    WHEN age < 60 THEN '50대'
    WHEN age < 70 THEN '60대'
    ELSE '70대이상'
  END AS age_group,
  sex,
  -- region_group
  CASE WHEN province IN ('서울','경기','인천') THEN '수도권' ELSE '비수도권' END AS region_group,
  -- family_group
  CASE
    WHEN family_type IN ('혼자 거주','혼자 거주 (배우자 별거)') THEN '1인가구'
    WHEN family_type = '배우자와 거주' THEN '부부가구'
    WHEN family_type = '배우자·자녀와 거주' THEN '부부+자녀'
    WHEN family_type IN ('자녀와 거주 (한부모)','자녀와 거주 (배우자 별거)') THEN '한부모'
    WHEN family_type IN ('부모와 동거','아버지와 동거','어머니와 동거') THEN '부모동거'
    ELSE '다세대·기타'
  END AS family_group,
  -- occupation_group
  COALESCE(oc.category, '기타') AS occupation_group,
  province,
  district,
  occupation,
  family_type
FROM persona p
LEFT JOIN occupation_category oc USING (occupation);

CREATE INDEX IF NOT EXISTS idx_cluster_key ON persona_cluster(age_group, sex, region_group, family_group, occupation_group);
CREATE INDEX IF NOT EXISTS idx_cluster_uuid ON persona_cluster(uuid);

-- ---------- 3) cluster_key 생성 + 집계 ----------
DROP TABLE IF EXISTS cluster_stats;
CREATE TABLE cluster_stats AS
SELECT
  'C' || lpad(CAST(row_number() OVER (ORDER BY count(*) DESC) AS text), 3, '0') AS cluster_id,
  age_group,
  sex,
  region_group,
  family_group,
  occupation_group,
  count(*) AS population,
  round(count(*)::numeric / 1000000, 6) AS population_ratio
FROM persona_cluster
GROUP BY 2,3,4,5,6;

CREATE INDEX IF NOT EXISTS idx_cluster_stats_id ON cluster_stats(cluster_id);
