import { Pool, PoolClient } from 'pg'

class DatabaseManager {
  private static instance: DatabaseManager
  private pool: Pool | null = null

  private constructor() {}

  public static getInstance(): DatabaseManager {
    if (!DatabaseManager.instance) {
      DatabaseManager.instance = new DatabaseManager()
    }
    return DatabaseManager.instance
  }

  public getPool(): Pool {
    if (!this.pool) {
      this.pool = new Pool({
        connectionString: process.env.DATABASE_URL,
        ssl: process.env.NODE_ENV === 'production' ? { rejectUnauthorized: false } : false,
        // 连接池配置
        max: 20,          // 最大连接数
        min: 2,           // 最小连接数
        idleTimeoutMillis: 30000,  // 空闲连接超时
        connectionTimeoutMillis: 5000,  // 获取连接超时
      })

      // 监听连接池事件
      this.pool.on('connect', () => {
        console.log('🔗 Database client connected')
      })

      this.pool.on('error', (err) => {
        console.error('❌ Database pool error:', err)
      })
    }
    return this.pool
  }

  // 自动管理连接的查询方法
  public async query(text: string, params?: any[]) {
    const pool = this.getPool()
    const client = await pool.connect()
    try {
      const result = await client.query(text, params)
      return result
    } finally {
      client.release() // 确保连接返回池中
    }
  }

  // 优雅关闭
  public async close() {
    if (this.pool) {
      await this.pool.end()
      this.pool = null
      console.log('🔌 Database pool closed')
    }
  }
}

// 导出单例实例的方法
const db = DatabaseManager.getInstance()
export const query = db.query.bind(db)
export const closeDatabase = db.close.bind(db)
export const testConnection = async () => {
  try {
    const result = await query('SELECT NOW()')
    console.log('✅ Database connected:', result.rows[0])
    return true
  } catch (error) {
    console.error('❌ Database connection failed:', error)
    return false
  }
}