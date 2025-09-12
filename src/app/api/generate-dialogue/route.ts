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
      script,
      teachingGoal,
      subject,
      grade
    } = await request.json()

    if (!sceneName || !characters || !dialogue) {
      return NextResponse.json(
        { error: '场景信息不完整' },
        { status: 400 }
      )
    }

    // 构建增强的对话生成prompt
    const dialoguePrompt = `
你是教育游戏对话设计师，基于以下信息生成8-15轮完整教学对话：

【基本信息】
场景：${sceneName}
学科：${subject || '未知'} (${grade || '未知'}年级)
教学目标：${teachingGoal || '未明确'}

【角色信息】
主角：${characters.主角?.角色名 || '主角'} - ${characters.主角?.性格 || ''}
NPC：${characters.NPC?.角色名 || 'NPC'} - ${characters.NPC?.性格 || ''}

【现有对话框架】
开场对话示例：${JSON.stringify(dialogue.开场对话 || [])}
学习对话示例：${JSON.stringify(dialogue.学习对话 || [])}
互动问答环节：${JSON.stringify(dialogue.互动问答环节 || dialogue.问答环节 || {})}

【剧本背景】
旁白：${script?.旁白 || ''}
情节描述：${script?.情节描述 || ''}
互动设计：${script?.互动设计 || ''}

请按以下格式输出完整多轮对话：
NPC: [对话内容]
玩家: [对话内容]
NPC: [对话内容]
玩家: [对话内容]
...

在对话末尾包含互动问答环节，根据教学以及互动需要选择以下互动方式之一：

【选择题形式】
问题：[NPC提问]
A. [选项A] B. [选项B] C. [选项C]
正确答案：[A/B/C]
正确反馈：[鼓励性回应和解释]
错误反馈：[引导性回应和提示]

【填空题形式】
问题：[NPC提问，包含空白处标记]
填空提示：[提示信息]
正确答案：[应填入的内容]
正确反馈：[表扬和解释]
错误反馈：[鼓励和提示]

【操作题形式】
问题：[NPC说明操作任务]
操作说明：[具体操作步骤]
成功标准：[完成的标准]
成功反馈：[表扬和总结]
失败反馈：[鼓励和指导]

【对话题形式】
问题引导：[NPC引导问题]
预期回答：[学生可能的回答]
深入问题：[进一步的问题]
总结反馈：[对整个对话的总结]

要求：
- 8-15轮对话，符合${grade || ''}年级理解水平
- 自然融入${subject || ''}学科知识点
- 对话要推进教学目标的达成
- 互动环节要符合场景背景和角色性格
- 语言生动有趣，适合教育游戏情境
- 根据互动需求选择最合适合理的互动方式
- **重要**：如果学生打错了的话，NPC要通过提示、类比、举例等方式引导学生往正确答案的方向思考。让学生通过思考过程自然得出答案
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