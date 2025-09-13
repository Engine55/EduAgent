import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const { imageUrl } = await request.json()

    if (!imageUrl) {
      return NextResponse.json(
        { error: '图片URL不能为空' },
        { status: 400 }
      )
    }

    console.log('📥 代理下载图片:', imageUrl)

    // 通过服务器端请求下载图片（绕过CORS限制）
    const response = await fetch(imageUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; NextJS-Proxy/1.0)',
      },
    })

    if (!response.ok) {
      console.error('图片下载失败:', response.status, response.statusText)
      return NextResponse.json(
        { error: `图片下载失败: ${response.status}` },
        { status: 500 }
      )
    }

    // 获取图片数据
    const imageBuffer = await response.arrayBuffer()
    
    // 获取Content-Type
    const contentType = response.headers.get('content-type') || 'image/png'
    
    console.log(`✅ 图片下载成功，大小: ${imageBuffer.byteLength} bytes`)

    // 直接返回图片二进制数据
    return new NextResponse(imageBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Length': imageBuffer.byteLength.toString(),
        'Cache-Control': 'public, max-age=3600', // 缓存1小时
      },
    })

  } catch (error: any) {
    console.error('图片代理下载错误:', error)
    
    return NextResponse.json(
      { 
        error: '图片下载失败',
        details: error.message 
      },
      { status: 500 }
    )
  }
}