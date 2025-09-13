// 测试数据库连接的简单脚本
const { PrismaClient } = require('@prisma/client')

const prisma = new PrismaClient()

async function testConnection() {
  try {
    console.log('🔄 Testing database connection...')
    
    // 测试基本连接
    await prisma.$connect()
    console.log('✅ Database connected successfully!')
    
    // 测试插入数据
    const testData = await prisma.eduData.create({
      data: {
        id: `test_${Date.now()}`,
        dataType: 'connection_test',
        userId: '1',
        data: {
          message: 'Database connection test successful!',
          timestamp: new Date().toISOString(),
          version: '1.0'
        }
      }
    })
    console.log('✅ Test data inserted:', testData.id)
    
    // 测试查询数据
    const count = await prisma.eduData.count()
    console.log(`✅ Total records in database: ${count}`)
    
    // 清理测试数据
    await prisma.eduData.delete({
      where: { id: testData.id }
    })
    console.log('✅ Test data cleaned up')
    
    console.log('🎉 Database setup completed successfully!')
    
  } catch (error) {
    console.error('❌ Database connection failed:', error)
    process.exit(1)
  } finally {
    await prisma.$disconnect()
  }
}

testConnection()