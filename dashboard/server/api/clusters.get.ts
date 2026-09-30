export default defineEventHandler(async (event) => {
  const pool = usePool()
  const r = await pool.query(
    'SELECT cluster_id, label, age_group, sex, region_group, family_group, occupation_group, population, population_ratio FROM cluster_stats ORDER BY population DESC LIMIT 20'
  )
  return { clusters: r.rows }
})
