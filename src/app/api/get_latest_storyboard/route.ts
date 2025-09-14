import { NextRequest, NextResponse } from 'next/server'

export async function GET() {
  try {
    console.log('📊 获取最新的故事板数据')

    const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/get_latest_storyboard`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    if (!response.ok) {
      throw new Error(`Backend responded with status: ${response.status}`)
    }

    const data = await response.json()

    if (data.success) {
      console.log('✅ 成功获取最新故事板数据')
      return NextResponse.json(data.data)
    } else {
      throw new Error(data.error || '获取最新故事板数据失败')
    }

  } catch (error) {
    console.error('获取最新故事板数据失败:', error)
    return NextResponse.json(
      {
        error: '获取最新故事板数据失败',
        details: error instanceof Error ? error.message : '未知错误'
      },
      { status: 500 }
    )
  }
}