export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const q = String(query.q || '')
  if (!q.trim()) return { results: [] }

  const pool = usePool()
  // LIKE 기반 의미 검색 폴백 (대시보드는 임베딩 없이 PostgreSQL 검색)
  const tokens = q.replace(/,/g, ' ').split(/\s+/).filter((t) => t.length >= 2)
  if (tokens.length === 0) return { results: [] }

  const patterns = tokens.map((t) => `%${t}%`)
  const r = await pool.query(
    `SELECT uuid, sex, age, province, district, occupation, persona
     FROM persona
     WHERE hobbies_and_interests ILIKE ANY($1)
        OR persona ILIKE ANY($1)
     LIMIT 10`,
    [patterns]
  )
  return { results: r.rows }
})
