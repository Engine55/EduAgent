import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function POST(request: NextRequest) {
  try {
    const { 
      sceneName, 
      characters, 
      dialogue,
      script 
    } = await request.json()

    if (!sceneName || !characters || !dialogue) {
      return NextResponse.json(
        { error: '场景信息不完整' },
        { status: 400 }
      )
    }

    // 构建简化的对话生成prompt
    const dialoguePrompt = `
基于以下信息，生成8-15轮完整对话：

场景：${sceneName}
角色：${characters.主角?.角色名 || '主角'} 和 ${characters.NPC?.角色名 || 'NPC'}

现有对话框架：
开场对话示例：${JSON.stringify(dialogue.开场对话 || [])}
学习对话示例：${JSON.stringify(dialogue.学习对话 || [])}
问答环节：${JSON.stringify(dialogue.问答环节 || {})}

请按以下格式输出完整多轮对话：
NPC: [对话内容]
玩家: [对话内容]
NPC: [对话内容]
玩家: [对话内容]
...

在对话末尾包含问答环节：
问题：[NPC提问]
A. [选项A]
B. [选项B]
正确答案：[A或B]
正确反馈：[鼓励性回应]
错误反馈：[引导性回应]

要求：
- 8-15轮对话
- 符合教育场景
- 自然流畅
- 包含知识点
`

    const response = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "user",
          content: dialoguePrompt
        }
      ],
      temperature: 0.7,
      max_tokens: 1500
    })

    const generatedDialogue = response.choices[0]?.message?.content

    if (!generatedDialogue) {
      return NextResponse.json(
        { error: '对话生成失败' },
        { status: 500 }
      )
    }

    return NextResponse.json({
      success: true,
      dialogue: generatedDialogue
    })

  } catch (error: any) {
    console.error('Dialogue generation error:', error)
    
    return NextResponse.json(
      { 
        error: '对话生成失败',
        details: error.message 
      },
      { status: 500 }
    )
  }
}