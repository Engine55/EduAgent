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

    // 构建基于storyboard的对话优化prompt
    const dialoguePrompt = `
你是专业的剧情驱动对话优化师。基于已生成的storyboard框架，对现有对话进行深度优化和扩展，生成完整的8-15轮沉浸式冒险对话。

【优化任务】
你需要分析现有的storyboard内容，识别其优势和不足，然后生成更加完善、连贯、沉浸的对话版本。

【场景设定】
- 场景名称：${sceneName}
- 学科领域：${subject || '未知'} (${grade || '未知'}年级)
- 教学目标：${teachingGoal || '未明确'}

【已建立的角色档案】
- 主角：${characters.主角?.角色名 || '主角'}
  外貌：${characters.主角?.外貌 || ''}
  性格：${characters.主角?.性格 || ''}
  特殊能力：${characters.主角?.特殊能力 || ''}

- NPC：${characters.NPC?.角色名 || 'NPC'}
  外貌：${characters.NPC?.外貌 || ''}
  性格：${characters.NPC?.性格 || ''}
  作用：${characters.NPC?.作用 || ''}

【现有故事框架（需要优化扩展）】
剧情背景：${script?.旁白 || ''}
核心情节：${script?.情节描述 || ''}
互动机制：${script?.互动设计 || ''}

【现有对话素材（需要深度改进）】
开场对话基础：${JSON.stringify(dialogue.开场对话 || [])}
探索对话基础：${JSON.stringify(dialogue.探索对话 || dialogue.学习对话 || [])}
互动解谜环节基础：${JSON.stringify(dialogue.互动解谜环节 || dialogue.互动问答环节 || dialogue.问答环节 || {})}

【优化重点】
1. **情感深度**：每句对话都要体现角色的真实情感状态和动机
2. **剧情张力**：逐步升级困境的紧迫感，让玩家感到真正的威胁和压力
3. **知识融合**：让${subject || ''}知识看起来像是这个世界的自然法则，而不是学习内容
4. **伙伴关系**：NPC和主角应该表现出真正的相互依赖和信任
5. **探索引导**：失败时的引导要自然而富有启发性，像真正的伙伴会做的那样

【输出完整对话】按以下格式生成8-15轮深度对话：

NPC: [结合角色性格和当前困境的具体对话]
玩家: [符合角色设定的回应]
NPC: [推进剧情和情感的对话]
玩家: [显示角色成长的回应]
...

【互动解谜环节】基于故事情境设计具体的知识考核：

**困境描述**：[NPC详细描述当前困境，暗示需要特定智慧解决]
**探索引导**：[NPC引导观察环境线索，发现解决思路]

**考核设计**：
- **考核类型**：根据互动需求选择（选择题/填空题/拖拽排序/数字输入/操作模拟等）
- **具体题目**：明确的问题表述，结合剧情情境
- **选项设置**：具体的选项内容或操作说明
- **正确答案**：标准答案
- **答案解析**：与${subject || ''}知识的关联说明

**三层次反馈**：
- **完全正确**：环境变化 + NPC兴奋 + 剧情奖励 + 关系深化
- **部分正确**：部分效果 + 具体提示 + 鼓励指导  
- **完全错误**：安全失败 + 学习线索 + 重试指导（直到成功）

【关键要求】：
- 对话必须推进主线剧情，不能是无意义的闲聊
- ${subject || ''}知识必须是解决困境的唯一有效方法
- 失败后的引导要让玩家有新的发现，而不是简单重复
- 成功后的奖励要对后续剧情有实际意义
- 全程维持角色设定的一致性和世界观的沉浸感
- 语言适合${grade || ''}年级但要有真正的情感深度
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