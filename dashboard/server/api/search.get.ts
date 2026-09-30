export default defineEventHandler(async (event) => {
  const query = getQuery(event)
  const pool = usePool()
  const where: string[] = []
  const params: any[] = []
  let i = 1

  const eq = (col: string, val: any) => {
    if (val) { where.push(`${col} = $${i++}`); params.push(val) }
  }
  const range = (col: string, min: any, max: any) => {
    if (min != null && min !== '') { where.push(`${col} >= $${i++}`); params.push(min) }
    if (max != null && max !== '') { where.push(`${col} <= $${i++}`); params.push(max) }
  }

  eq('sex', query.sex)
  eq('province', query.province)
  eq('district', query.district)
  eq('occupation', query.occupation)
  eq('family_type', query.family_type)
  range('age', query.age_min, query.age_max)

  const cond = where.length ? ' WHERE ' + where.join(' AND ') : ''
  const limit = Math.min(parseInt(String(query.limit || '20')), 100)

  const r = await pool.query(
    `SELECT uuid, sex, age, province, district, occupation, family_type, housing_type, marital_status, education_level, persona
     FROM persona${cond} LIMIT ${limit}`,
    params
  )
  return { count: r.rows.length, results: r.rows }
})
