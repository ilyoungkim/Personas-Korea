import pg from 'pg'

const { Pool } = pg

let _pool: pg.Pool | null = null

export function usePool(): pg.Pool {
  if (!_pool) {
    const config = useRuntimeConfig()
    _pool = new Pool({ connectionString: config.pgDsn, max: 10 })
  }
  return _pool
}
