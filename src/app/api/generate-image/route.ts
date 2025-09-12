import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function POST(request: NextRequest) {
  try {
    const { imagePrompt, nodeId } = await request.json()

    if (!imagePrompt) {
      return NextResponse.json(
        { error: '图片提示词不能为空' },
        { status: 400 }
      )
    }

    // 构建完整的提示词
    let fullPrompt = ''
    
    if (typeof imagePrompt === 'string') {
      fullPrompt = imagePrompt
    } else {
      // 如果是对象，组合各个部分
      const parts = []
      if (imagePrompt.场景描述) parts.push(`场景: ${imagePrompt.场景描述}`)
      if (imagePrompt.视觉风格) parts.push(`风格: ${imagePrompt.视觉风格}`)
      if (imagePrompt.角色描述) parts.push(`角色: ${imagePrompt.角色描述}`)
      if (imagePrompt.构图要求) parts.push(`构图: ${imagePrompt.构图要求}`)
      if (imagePrompt.技术参数) parts.push(`技术参数: ${imagePrompt.技术参数}`)
      
      fullPrompt = parts.join(', ')
    }

    // 调用DALL-E 3生成图片
    const response = await openai.images.generate({
      model: "dall-e-3",
      prompt: fullPrompt,
      n: 1,
      size: "1024x1024",
      quality: "standard",
    })

    const imageUrl = response.data[0]?.url

    if (!imageUrl) {
      return NextResponse.json(
        { error: '图片生成失败' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      imageUrl,
      nodeId,
      prompt: fullPrompt
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