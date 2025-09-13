import { NextRequest, NextResponse } from 'next/server'

const LOUDLY_API_KEY = process.env.LOUDLY_API_KEY || "2V98aHDlehFLYlpa4ZJpdopUuPByi6iK8EtGviSJEqw"
const LOUDLY_BASE_URL = "https://soundtracks.loudly.com"
const OPENAI_API_KEY = process.env.OPENAI_API_KEY

export async function POST(request: NextRequest) {
  try {
    const { imagePrompt, sceneName, duration = 60 } = await request.json()

    if (!imagePrompt) {
      return NextResponse.json(
        { error: '场景提示词不能为空' },
        { status: 400 }
      )
    }

    console.log('🎵 为场景生成音乐:', sceneName, '| 提示词:', imagePrompt)

    // 使用AI将图片提示词转换为音乐提示词
    const musicPrompt = await convertImagePromptWithAI(imagePrompt, sceneName)
    
    const headers = {
      "API-KEY": LOUDLY_API_KEY,
    }

    const formData = {
      "prompt": musicPrompt,
      "duration": duration,
      "test": true, // 先用测试模式
      "structure_id": 0
    }

    console.log('🎶 音乐生成参数:', formData)

    // 调用Loudly API生成音乐
    const response = await fetch(`${LOUDLY_BASE_URL}/api/ai/prompt/songs`, {
      method: 'POST',
      headers,
      body: new URLSearchParams(formData as any)
    })

    if (!response.ok) {
      console.error('Loudly API错误:', response.status, await response.text())
      return NextResponse.json(
        { error: `音乐生成失败: ${response.status}` },
        { status: 500 }
      )
    }

    const result = await response.json()
    console.log('✅ Loudly API响应:', result)

    const audioUrl = result.music_file_path
    if (!audioUrl) {
      return NextResponse.json(
        { error: '未获得音频文件URL' },
        { status: 500 }
      )
    }

    console.log('🎵 音频URL:', audioUrl)

    // 直接下载音频并返回MP3二进制数据
    console.log('📥 下载生成的音频文件...')
    const audioResponse = await fetch(audioUrl, {
      method: 'GET',
      headers: {
        'User-Agent': 'Mozilla/5.0 (compatible; NextJS-Proxy/1.0)',
      },
    })

    if (!audioResponse.ok) {
      return NextResponse.json(
        { error: `音频下载失败: ${audioResponse.status}` },
        { status: 500 }
      )
    }

    const audioBuffer = await audioResponse.arrayBuffer()
    
    console.log(`✅ 音乐生成并下载成功，大小: ${audioBuffer.byteLength} bytes`)

    // 直接返回MP3二进制数据
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': 'audio/mpeg',
        'Content-Length': audioBuffer.byteLength.toString(),
        'Cache-Control': 'public, max-age=3600',
      },
    })

  } catch (error: any) {
    console.error('音乐生成错误:', error)
    
    return NextResponse.json(
      { 
        error: '音乐生成失败',
        details: error.message 
      },
      { status: 500 }
    )
  }
}

// 使用AI将图片提示词转换为音乐提示词
async function convertImagePromptWithAI(imagePrompt: string, sceneName?: string): Promise<string> {
  if (!OPENAI_API_KEY) {
    // 如果没有OpenAI API Key，使用简单备用逻辑
    return `ambient background music for educational RPG game scene: ${sceneName || 'learning adventure'}, gentle and engaging atmosphere`
  }

  try {
    const prompt = typeof imagePrompt === 'string' ? imagePrompt : JSON.stringify(imagePrompt)
    
    const response = await fetch('https://api.openai.com/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${OPENAI_API_KEY}`,
      },
      body: JSON.stringify({
        model: "gpt-4o-mini",
        messages: [{
          role: "system",
          content: "你是一个专业的音乐制作专家，擅长将视觉场景描述转换为音乐风格描述。请将图片提示词转换为适合教育RPG游戏的背景音乐描述，使用英文回复，要求音乐适合儿童教育环境，氛围温和而富有吸引力。"
        }, {
          role: "user", 
          content: `场景名称：${sceneName}\n图片描述：${prompt}\n\n请将这个视觉场景转换为音乐描述，要求：\n1. 适合教育RPG游戏背景音乐\n2. 符合场景氛围\n3. 适合儿童学习环境\n4. 用英文描述\n5. 直接输出音乐描述，不要其他内容`
        }],
        max_tokens: 150,
        temperature: 0.7
      })
    })

    if (response.ok) {
      const result = await response.json()
      const musicPrompt = result.choices[0]?.message?.content?.trim()
      
      if (musicPrompt) {
        console.log('🤖 AI转换结果:', musicPrompt)
        return musicPrompt
      }
    }
  } catch (error) {
    console.error('AI转换失败，使用备用方法:', error)
  }

  // 简单备用逻辑
  return `ambient background music for educational RPG game scene: ${sceneName || 'learning adventure'}, gentle and engaging atmosphere`
}