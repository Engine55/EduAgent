import { NextRequest, NextResponse } from 'next/server'

const OPENAI_API_KEY = process.env.OPENAI_API_KEY

export async function POST(request: NextRequest) {
  try {
    const { imagePrompt, nodeId } = await request.json()

    if (!imagePrompt) {
      return NextResponse.json(
        { error: '图片提示词不能为空' },
        { status: 400 }
      )
    }

    if (!OPENAI_API_KEY) {
      return NextResponse.json(
        { error: 'OpenAI API密钥未配置' },
        { status: 500 }
      )
    }

    // 构建完整的提示词
    let fullPrompt = ''

    if (typeof imagePrompt === 'string') {
      fullPrompt = imagePrompt
    } else {
      const parts = []
      if (imagePrompt.场景描述) parts.push(`Scene: ${imagePrompt.场景描述}`)
      if (imagePrompt.视觉风格) parts.push(`Style: ${imagePrompt.视觉风格}`)
      if (imagePrompt.角色描述) parts.push(`Characters: ${imagePrompt.角色描述}`)
      if (imagePrompt.构图要求) parts.push(`Composition: ${imagePrompt.构图要求}`)
      if (imagePrompt.技术参数) parts.push(`Technical: ${imagePrompt.技术参数}`)

      fullPrompt = parts.join(', ')
    }

    console.log('🎨 使用DALL-E 3生成图片:', fullPrompt)

    // 调用OpenAI DALL-E 3 API
    const response = await fetch('https://api.openai.com/v1/images/generations', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "dall-e-3",
        prompt: `pixel art RPG style, high resolution game art, ${fullPrompt}, no extra people, no background characters, clean composition`,
        n: 1,
        size: "1024x1024",
        quality: "standard",
        response_format: "url"
      })
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      console.error('OpenAI API error:', response.status, errorData)

      return NextResponse.json(
        {
          error: `图片生成失败 (${response.status})`,
          details: errorData.error?.message || '未知错误'
        },
        { status: 500 }
      )
    }

    const data = await response.json()
    console.log('🔍 DALL-E 3 API响应结构:', Object.keys(data))

    // DALL-E 3返回格式: { data: [{ url: "..." }] }
    const imageUrl = data.data?.[0]?.url

    if (!imageUrl) {
      console.error('No image URL in response:', data)
      return NextResponse.json(
        { error: '图片生成失败：未返回图片URL' },
        { status: 500 }
      )
    }

    console.log('✅ 获取到图片URL:', imageUrl)

    return NextResponse.json({
      success: true,
      imageUrl: imageUrl,
      nodeId,
      prompt: fullPrompt,
      model: 'dall-e-3',
      imageType: 'url'
    })

  } catch (error: any) {
    console.error('Image generation error:', error)
    
    return NextResponse.json(
      { 
        error: '图片生成失败',
        details: error.message 
      },
      { status: 500 }
    )
  }
}