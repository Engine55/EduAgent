import { NextRequest, NextResponse } from 'next/server'
import fs from 'fs'
import path from 'path'

const OPENAI_API_KEY = process.env.OPENAI_API_KEY

export async function POST(request: NextRequest) {
  try {
    const { imagePrompt, sceneName } = await request.json()

    if (!imagePrompt) {
      return NextResponse.json(
        { error: '场景提示词不能为空' },
        { status: 400 }
      )
    }

    console.log('🎵 为场景匹配音乐:', sceneName, '| 提示词:', imagePrompt)

    // 从MP3文件夹中找到最匹配的音乐文件
    const selectedMusicFile = await findBestMatchingMusic(imagePrompt, sceneName)
    
    if (!selectedMusicFile) {
      return NextResponse.json(
        { error: '未找到合适的音乐文件' },
        { status: 404 }
      )
    }

    console.log('🎶 选择的音乐文件:', selectedMusicFile)

    // 读取并返回MP3文件
    const musicFilePath = path.join(process.cwd(), 'mp3folder', selectedMusicFile)
    
    if (!fs.existsSync(musicFilePath)) {
      return NextResponse.json(
        { error: '音乐文件不存在' },
        { status: 404 }
      )
    }

    const audioBuffer = fs.readFileSync(musicFilePath)
    
    // 根据文件扩展名确定Content-Type
    const isWav = selectedMusicFile.toLowerCase().endsWith('.wav')
    const contentType = isWav ? 'audio/wav' : 'audio/mpeg'
    
    console.log(`✅ 返回音乐文件: ${selectedMusicFile}, 大小: ${audioBuffer.byteLength} bytes`)

    // 直接返回音频二进制数据
    return new NextResponse(audioBuffer, {
      headers: {
        'Content-Type': contentType,
        'Content-Length': audioBuffer.byteLength.toString(),
        'Cache-Control': 'public, max-age=3600',
      },
    })

  } catch (error: any) {
    console.error('音乐匹配错误:', error)
    
    return NextResponse.json(
      { 
        error: '音乐匹配失败',
        details: error.message 
      },
      { status: 500 }
    )
  }
}

// 找到最匹配的音乐文件
async function findBestMatchingMusic(imagePrompt: string, sceneName?: string): Promise<string | null> {
  try {
    // 获取MP3文件夹中的所有mp3文件
    const mp3FolderPath = path.join(process.cwd(), 'mp3folder')
    
    if (!fs.existsSync(mp3FolderPath)) {
      console.error('mp3folder 不存在')
      return null
    }

    const files = fs.readdirSync(mp3FolderPath).filter(file => {
      const ext = file.toLowerCase()
      return ext.endsWith('.mp3') || ext.endsWith('.wav')
    })

    if (files.length === 0) {
      console.error('mp3folder 中没有找到音频文件')
      return null
    }

    console.log('🎵 找到的MP3文件:', files)

    // 如果只有一个文件，直接返回
    if (files.length === 1) {
      return files[0]
    }

    // 使用AI来分析并匹配最合适的音乐文件
    const musicPrompt = await convertImagePromptWithAI(imagePrompt, sceneName)
    const bestMatch = await selectBestMusicWithAI(musicPrompt, files)
    
    return bestMatch || files[0] // 如果AI匹配失败，返回第一个文件作为备选
  } catch (error) {
    console.error('音乐文件匹配失败:', error)
    return null
  }
}

// 使用AI选择最合适的音乐文件
async function selectBestMusicWithAI(musicDescription: string, availableFiles: string[]): Promise<string | null> {
  if (!OPENAI_API_KEY) {
    // 如果没有API Key，使用简单的关键词匹配
    return simpleKeywordMatch(musicDescription, availableFiles)
  }

  try {
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
          content: "你是一个专业的音乐匹配专家。根据音乐描述和可用的音乐文件列表，选择最合适的一个文件。只返回文件名，不要其他内容。"
        }, {
          role: "user", 
          content: `音乐描述：${musicDescription}\n\n可用的音乐文件：\n${availableFiles.map((f, i) => `${i + 1}. ${f}`).join('\n')}\n\n请选择最合适的文件名（只返回文件名）：`
        }],
        max_tokens: 50,
        temperature: 0.3
      })
    })

    if (response.ok) {
      const result = await response.json()
      const selectedFile = result.choices[0]?.message?.content?.trim()
      
      // 验证返回的文件名是否在列表中
      if (selectedFile && availableFiles.includes(selectedFile)) {
        console.log('🤖 AI选择的音乐文件:', selectedFile)
        return selectedFile
      } else {
        console.log('AI返回的文件名无效，使用关键词匹配:', selectedFile)
        return simpleKeywordMatch(musicDescription, availableFiles)
      }
    }
  } catch (error) {
    console.error('AI音乐匹配失败，使用关键词匹配:', error)
  }

  return simpleKeywordMatch(musicDescription, availableFiles)
}

// 简单的关键词匹配备选方案
function simpleKeywordMatch(description: string, files: string[]): string {
  const desc = description.toLowerCase()
  
  // 定义关键词映射，根据现有文件名优化
  const keywordMap = {
    'forest': ['forest', 'nature', 'woods', 'trees', 'ambient', 'forgotten', 'misty', 'bog', 'chase'],
    'village': ['village', 'town', 'folk', 'community', 'simple'],
    'mountain': ['mountain', 'high', 'peak', 'climb', 'elevation'],
    'battle': ['battle', 'fight', 'combat', 'action', 'intense', 'climax', 'rpg-battle'],
    'magic': ['magic', 'spell', 'wizard', 'practice', 'practicing', 'magical'],
    'map': ['map', 'travel', 'journey', 'navigation', 'exploration'],
    'peaceful': ['peaceful', 'calm', 'serene', 'gentle', 'soft'],
    'adventure': ['adventure', 'explore', 'journey', 'quest', 'epic'],
    'mystery': ['mystery', 'puzzle', 'enigma', 'dark', 'suspense', 'misty'],
    'happy': ['happy', 'cheerful', 'joy', 'bright', 'upbeat'],
    'sad': ['sad', 'melancholy', 'somber', 'emotional', 'slow']
  }

  // 为每个文件计算匹配分数
  let bestFile = files[0]
  let bestScore = 0

  for (const file of files) {
    const fileName = file.toLowerCase()
    let score = 0

    // 检查每个关键词类别
    for (const [category, keywords] of Object.entries(keywordMap)) {
      for (const keyword of keywords) {
        if (desc.includes(keyword) && fileName.includes(keyword)) {
          score += 3 // 精确匹配得高分
        } else if (desc.includes(keyword) && fileName.includes(category)) {
          score += 2 // 类别匹配得中分
        } else if (fileName.includes(keyword)) {
          score += 1 // 部分匹配得低分
        }
      }
    }

    if (score > bestScore) {
      bestScore = score
      bestFile = file
    }
  }

  console.log('🔍 关键词匹配选择的文件:', bestFile, '匹配分数:', bestScore)
  return bestFile
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