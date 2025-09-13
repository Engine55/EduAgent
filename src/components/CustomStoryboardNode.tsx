import React, { useState } from 'react'
import Image from 'next/image'
import { Handle, Position } from 'reactflow'

interface NodeData {
  sceneName: string
  stageId: string
  characters: {
    主角?: {
      角色名: string
      外貌: string
      性格: string
      特殊能力?: string
    }
    NPC?: {
      角色名: string
      外貌: string
      性格: string
      作用: string
    }
  }
  dialogue: {
    开场对话?: Array<{
      角色: string
      内容: string
    }>
    探索对话?: Array<{
      角色: string
      内容: string
    }>
    互动解谜环节?: {
      困境描述: string
      探索引导: string
      考核设计: {
        考核类型: string
        题目描述: string
        具体题目: string
        选项设置: string
        正确答案: string
        答案解析: string
      }
      反馈机制: {
        完全正确: {
          immediate_result: string
          npc_reaction: string
          story_reward: string
          relationship_change: string
        }
        部分正确: {
          partial_result: string
          hint_provision: string
          encouragement: string
        }
        完全错误: {
          safe_failure: string
          learning_clue: string
          retry_guidance: string
        }
      }
    }
    场景转换?: { [key: string]: string }
  }
  script: {
    旁白: string
    情节描述: string
    互动设计: string
  }
  imagePrompt: string | {
    视觉风格?: string
    场景描述?: string
    角色描述?: string
    构图要求?: string
    技术参数?: string
  }
  sceneInfo: {
    分镜编号: string
    场景类型: string
    时长估计: string
    关键事件: string
  }
  teachingGoal?: string
  subject?: string
  grade?: string
}

interface CustomStoryboardNodeProps {
  data: NodeData
}

const CustomStoryboardNode: React.FC<CustomStoryboardNodeProps> = ({ data }) => {
  const [showDialogue, setShowDialogue] = useState(false)
  const [showScript, setShowScript] = useState(false)
  const [generatedImage, setGeneratedImage] = useState<string | null>(null)
  const [isGeneratingImage, setIsGeneratingImage] = useState(false)
  const [imageError, setImageError] = useState<string | null>(null)
  const [generatedDialogue, setGeneratedDialogue] = useState<string | null>(null)
  const [isGeneratingDialogue, setIsGeneratingDialogue] = useState(false)
  const [dialogueError, setDialogueError] = useState<string | null>(null)

  const handleGenerateImage = async () => {
    if (!data.imagePrompt || isGeneratingImage) return

    setIsGeneratingImage(true)
    setImageError(null)

    try {
      const response = await fetch('/api/generate-image', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          imagePrompt: data.imagePrompt,
          nodeId: data.sceneInfo.分镜编号,
        }),
      })

      const result = await response.json()

      if (result.success) {
        setGeneratedImage(result.imageUrl)
      } else {
        setImageError(result.error || '图片生成失败')
      }
    } catch (error) {
      console.error('Image generation failed:', error)
      setImageError('图片生成失败，请稍后重试')
    } finally {
      setIsGeneratingImage(false)
    }
  }

  const downloadDialogue = (dialogueContent: string) => {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
    const filename = `dialogue_${data.sceneName}_${timestamp}.txt`
    
    const content = `场景：${data.sceneName}\n` +
                   `学科：${data.subject || '未知'} (${data.grade || '未知'}年级)\n` +
                   `教学目标：${data.teachingGoal || '未明确'}\n` +
                   `生成时间：${new Date().toLocaleString()}\n` +
                   `\n${'='.repeat(50)}\n\n` +
                   dialogueContent
    
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  const handleGenerateDialogue = async () => {
    if (isGeneratingDialogue) return

    setIsGeneratingDialogue(true)
    setDialogueError(null)

    try {
      const response = await fetch('/api/generate-dialogue', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sceneName: data.sceneName,
          characters: data.characters,
          dialogue: data.dialogue,
          script: data.script,
          teachingGoal: data.teachingGoal,
          subject: data.subject,
          grade: data.grade,
        }),
      })

      const result = await response.json()

      if (result.success) {
        setGeneratedDialogue(result.dialogue)
        setShowDialogue(true)
        // 自动下载对话文件
        downloadDialogue(result.dialogue)
      } else {
        setDialogueError(result.error || '对话生成失败')
      }
    } catch (error) {
      console.error('Dialogue generation failed:', error)
      setDialogueError('对话生成失败，请稍后重试')
    } finally {
      setIsGeneratingDialogue(false)
    }
  }

  return (
    <div className="bg-white border-2 border-purple-300 rounded-lg shadow-lg min-w-[380px] max-w-[420px] min-h-[800px] flex flex-col">
      <Handle type="target" position={Position.Top} />
      
      {/* 节点标题 */}
      <div className="p-3 border-b border-gray-200">
        <h3 className="text-lg font-bold text-purple-700 mb-1">{data.stageId}-{data.sceneName}</h3>
        <p className="text-xs text-gray-600">{data.sceneInfo.场景类型} | {data.sceneInfo.时长估计}</p>
      </div>
      
      {/* 第一块：图片区域 */}
      <div className="p-3 border-b border-gray-200 bg-gray-50 h-299">
        {generatedImage ? (
          <div className="w-full h-full relative rounded overflow-hidden">
            <Image 
              src={generatedImage} 
              alt="Generated scene image" 
              fill
              className="object-cover"
            />
            <button 
              className="absolute top-1 right-1 px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors opacity-80"
              onClick={handleGenerateImage}
              disabled={isGeneratingImage}
            >
              重新生成
            </button>
          </div>
        ) : (
          <div className="w-full h-full bg-gray-200 rounded border-2 border-dashed border-gray-300 flex flex-col items-center justify-center">
            {isGeneratingImage ? (
              <div className="flex flex-col items-center">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500 mb-2"></div>
                <div className="text-xs text-gray-500">生成中...</div>
              </div>
            ) : (
              <>
                <div className="text-xs text-gray-500 mb-2 text-center">
                  {imageError ? (
                    <span className="text-red-500">{imageError}</span>
                  ) : (
                    '场景图片'
                  )}
                </div>
                <button 
                  className="px-3 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors disabled:bg-gray-400"
                  onClick={handleGenerateImage}
                  disabled={!data.imagePrompt}
                >
                  Generate Image
                </button>
              </>
            )}
          </div>
        )}</div>
      
      {/* 第二块：剧本段落 */}
      <div className="p-3 border-b border-gray-200">
        <div className="flex justify-between items-center mb-2">
          <h4 className="font-semibold text-gray-800 text-sm">剧本</h4>
          <button 
            className="px-2 py-1 bg-gray-500 text-white text-xs rounded hover:bg-gray-600 transition-colors"
            onClick={() => setShowScript(!showScript)}
          >
            {showScript ? '收起' : '展开'}剧本
          </button>
        </div>
        {showScript && (
          <div className="space-y-1 text-xs select-text">
            <div className="p-1.5 bg-yellow-50 rounded">
              <p className="text-gray-700 leading-snug select-text cursor-text">{data.script.旁白}</p>
            </div>
            <div className="p-1.5 bg-blue-50 rounded">
              <p className="text-gray-700 leading-snug select-text cursor-text">{data.script.情节描述}</p>
            </div>
            <div className="p-1.5 bg-green-50 rounded">
              <p className="text-gray-700 leading-snug select-text cursor-text">{data.script.互动设计}</p>
            </div>
          </div>
        )}
      </div>
      
      {/* 第三块：角色介绍 */}
      <div className="p-3 border-b border-gray-200">
        <h4 className="font-semibold text-gray-800 mb-2 text-sm">角色介绍</h4>
        <div className="space-y-2">
          {data.characters.主角 && (
            <div className="p-2 bg-blue-50 rounded text-xs">
              <div className="font-medium text-blue-700 mb-1">{data.characters.主角.角色名}</div>
              <div className="text-gray-600">{data.characters.主角.外貌}</div>
            </div>
          )}
          {data.characters.NPC && (
            <div className="p-2 bg-green-50 rounded text-xs">
              <div className="font-medium text-green-700 mb-1">{data.characters.NPC.角色名}</div>
              <div className="text-gray-600">{data.characters.NPC.外貌}</div>
            </div>
          )}
        </div>
      </div>
      
      {/* 第四块：对话区域 */}
      <div className="p-3">
        <div className="flex justify-between items-center mb-2">
          <h4 className="font-semibold text-gray-800 text-sm">对话</h4>
          <div className="flex gap-1">
            {!generatedDialogue && (
              <button 
                className="px-2 py-1 bg-green-500 text-white text-xs rounded hover:bg-green-600 transition-colors disabled:bg-gray-400"
                onClick={handleGenerateDialogue}
                disabled={isGeneratingDialogue}
              >
                {isGeneratingDialogue ? '生成中...' : '生成对话'}
              </button>
            )}
            {generatedDialogue && (
              <button 
                className="px-2 py-1 bg-blue-500 text-white text-xs rounded hover:bg-blue-600 transition-colors"
                onClick={() => downloadDialogue(generatedDialogue)}
              >
                下载对话
              </button>
            )}
            <button 
              className="px-2 py-1 bg-purple-500 text-white text-xs rounded hover:bg-purple-600 transition-colors"
              onClick={() => setShowDialogue(!showDialogue)}
              disabled={!generatedDialogue && !isGeneratingDialogue}
            >
              {showDialogue ? '隐藏' : '显示'}对话
            </button>
          </div>
        </div>
        {showDialogue && (
          <div className="mt-2 p-3 bg-purple-50 rounded text-xs max-h-40 overflow-y-auto select-text">
            {isGeneratingDialogue ? (
              <div className="flex items-center justify-center py-4">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-purple-500 mr-2"></div>
                <span className="text-purple-600">生成对话中...</span>
              </div>
            ) : generatedDialogue ? (
              <div className="whitespace-pre-line text-gray-700 leading-relaxed select-text cursor-text">
                {generatedDialogue}
              </div>
            ) : dialogueError ? (
              <div className="text-red-500 text-center py-2">
                {dialogueError}
              </div>
            ) : (
              <div className="text-gray-500 text-center py-2">
                点击&quot;生成对话&quot;按钮创建完整对话
              </div>
            )}
          </div>
        )}
      </div>
      
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
}

export default CustomStoryboardNode