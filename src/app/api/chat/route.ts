import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { message } = await request.json()

    if (!message || typeof message !== 'string') {
      return NextResponse.json(
        { success: false, error: '消息内容不能为空' },
        { status: 400 }
      )
    }

    // 这里需要调用你的Python后端服务
    // 暂时先返回模拟响应
    const mockResponse = {
      success: true,
      response: `我收到了您的消息: "${message}"\n\n这是一个模拟回复。请配置Python后端连接以获得真实的AI回复。`,
      ready_for_stage2: false,
      stage: 'stage1_collecting',
      requirement_id: null
    }

    // TODO: 替换为真实的Python后端调用
    // const pythonBackendResponse = await fetch('http://localhost:8000/chat', {
    //   method: 'POST',
    //   headers: {
    //     'Content-Type': 'application/json',
    //   },
    //   body: JSON.stringify({ message }),
    // })
    // 
    // if (!pythonBackendResponse.ok) {
    //   throw new Error('Python后端调用失败')
    // }
    // 
    // const result = await pythonBackendResponse.json()
    // return NextResponse.json(result)

    // 暂时返回模拟响应
    return NextResponse.json(mockResponse)

  } catch (error: any) {
    console.error('Chat API error:', error)
    
    return NextResponse.json(
      { 
        success: false, 
        error: '处理消息时出现错误',
        details: error.message 
      },
      { status: 500 }
    )
  }
}