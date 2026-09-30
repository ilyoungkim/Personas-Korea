export default defineEventHandler(async (event) => {
  const pool = usePool()
  const r = await pool.query('SELECT count(*)::int AS total FROM persona')
  const total = r.rows[0].total
  const prov = await pool.query(
    'SELECT province AS key, count(*)::int AS cnt FROM persona GROUP BY province ORDER BY cnt DESC'
  )
  const sex = await pool.query(
    'SELECT sex AS key, count(*)::int AS cnt FROM persona GROUP BY sex ORDER BY cnt DESC'
  )
  const age = await pool.query(
    "SELECT CASE WHEN age<20 THEN '10대' WHEN age<30 THEN '20대' WHEN age<40 THEN '30대' WHEN age<50 THEN '40대' WHEN age<60 THEN '50대' WHEN age<70 THEN '60대' ELSE '70대이상' END AS key, count(*)::int AS cnt FROM persona GROUP BY key ORDER BY key"
  )
  return {
    total,
    province: prov.rows,
    sex: sex.rows,
    age: age.rows,
  }
})
