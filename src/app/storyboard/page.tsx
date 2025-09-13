'use client'

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import JSZip from 'jszip'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'
import CustomStoryboardNode from '@/components/CustomStoryboardNode'

const nodeTypes: NodeTypes = {
  storyboard: CustomStoryboardNode,
}

interface StoryboardData {
  分镜基础信息: {
    分镜编号: string
    场景类型: string
    时长估计: string
    关键事件: string
  }
  人物档案: any
  人物对话: any
  剧本: any
  图片提示词?: string | {
    视觉风格?: string
    场景描述?: string
    角色描述?: string
    构图要求?: string
    技术参数?: string
  }
  场景转换?: { [key: string]: string }
}

interface StoryData {
  story_id: string
  story_title: string
  subject?: string
  grade?: string
  storyboards: Array<{
    stage_index: number
    stage_name: string
    stage_id: string
    storyboard: StoryboardData
    teachingGoal?: string
    // 新增：预生成的内容
    generated_image_data?: {
      base64_data: string
      file_extension: string
      original_url: string
    }
    generated_image_url?: string
    generated_dialogue?: string
    generation_status?: {
      storyboard: 'success' | 'failed'
      image: 'success' | 'failed'
      dialogue: 'success' | 'failed'
    }
  }>
}

export default function StoryboardPage() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [isLoading, setIsLoading] = useState(true)
  const [storyData, setStoryData] = useState<StoryData | null>(null)
  const [isDownloading, setIsDownloading] = useState(false)

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  const downloadStoryboardPackage = async () => {
    if (!storyData) return

    setIsDownloading(true)
    try {
      const zip = new JSZip()
      
      // 为每个分镜创建文件夹和文件
      for (const storyboard of storyData.storyboards) {
        const folderName = `scene_${storyboard.stage_id}_${storyboard.stage_name}`
        const sceneFolder = zip.folder(folderName)
        
        if (!sceneFolder) continue

        // 1. 对话文件
        if (storyboard.generated_dialogue) {
          const dialogueContent = `场景：${storyboard.stage_name}\n` +
            `学科：${storyData.subject || '未知'} (${storyData.grade || '未知'}年级)\n` +
            `生成时间：${new Date().toLocaleString()}\n` +
            `\n${'='.repeat(50)}\n\n` +
            storyboard.generated_dialogue
          sceneFolder.file('对话.txt', dialogueContent)
        }

        // 2. 剧本文件
        if (storyboard.storyboard.剧本) {
          const scriptContent = `场景：${storyboard.stage_name}\n` +
            `分镜编号：${storyboard.storyboard.分镜基础信息?.分镜编号 || storyboard.stage_id}\n` +
            `场景类型：${storyboard.storyboard.分镜基础信息?.场景类型 || '未知'}\n` +
            `时长估计：${storyboard.storyboard.分镜基础信息?.时长估计 || '未知'}\n` +
            `\n${'='.repeat(50)}\n\n` +
            `【旁白】\n${storyboard.storyboard.剧本.旁白 || ''}\n\n` +
            `【情节描述】\n${storyboard.storyboard.剧本.情节描述 || ''}\n\n` +
            `【互动设计】\n${storyboard.storyboard.剧本.互动设计 || ''}`
          sceneFolder.file('剧本.txt', scriptContent)
        }

        // 3. 角色介绍文件
        if (storyboard.storyboard.人物档案) {
          const charactersContent = `场景：${storyboard.stage_name}\n` +
            `角色介绍\n` +
            `${'='.repeat(50)}\n\n` +
            `【主角】\n` +
            `角色名：${storyboard.storyboard.人物档案.主角?.角色名 || '未知'}\n` +
            `外貌：${storyboard.storyboard.人物档案.主角?.外貌 || '未描述'}\n` +
            `性格：${storyboard.storyboard.人物档案.主角?.性格 || '未描述'}\n` +
            `当前状态：${storyboard.storyboard.人物档案.主角?.当前状态 || '未描述'}\n\n` +
            `【NPC】\n` +
            `角色名：${storyboard.storyboard.人物档案.NPC?.角色名 || '未知'}\n` +
            `外貌：${storyboard.storyboard.人物档案.NPC?.外貌 || '未描述'}\n` +
            `性格：${storyboard.storyboard.人物档案.NPC?.性格 || '未描述'}\n` +
            `当前状态：${storyboard.storyboard.人物档案.NPC?.当前状态 || '未描述'}\n` +
            `与主角关系：${storyboard.storyboard.人物档案.NPC?.与主角关系 || '未描述'}`
          sceneFolder.file('角色介绍.txt', charactersContent)
        }

        // 4. 图片文件（如果有的话）
        if (storyboard.generated_image_url) {
          try {
            // 通过Next.js API代理下载图片（绕过CORS限制）
            const imageResponse = await fetch('/api/download-image', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                imageUrl: storyboard.generated_image_url
              })
            })
            
            if (imageResponse.ok) {
              const imageBlob = await imageResponse.blob()
              const contentType = imageResponse.headers.get('content-type') || 'image/png'
              const fileName = contentType.includes('jpeg') || contentType.includes('jpg') 
                ? '图片.jpg' 
                : '图片.png'
              
              sceneFolder.file(fileName, imageBlob)
              console.log(`✅ 添加图片文件: ${fileName}`)
            } else {
              // API下载失败，创建URL文件作为备选
              sceneFolder.file('图片_URL.txt', storyboard.generated_image_url)
            }
          } catch (error) {
            console.error(`下载图片失败 ${storyboard.stage_id}:`, error)
            // 创建一个URL文件作为备选
            sceneFolder.file('图片_URL.txt', storyboard.generated_image_url)
          }
        }

        // 5. 背景音乐文件
        if (storyboard.storyboard.图片提示词) {
          try {
            console.log(`🎵 为 ${storyboard.stage_name} 生成背景音乐...`)
            
            const musicResponse = await fetch('/api/generate-music', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({
                imagePrompt: storyboard.storyboard.图片提示词,
                sceneName: storyboard.stage_name,
                duration: 60 // 60秒背景音乐
              })
            })
            
            if (musicResponse.ok) {
              const musicBlob = await musicResponse.blob()
              const fileName = '背景音乐.mp3'
              
              sceneFolder.file(fileName, musicBlob)
              console.log(`✅ 添加音乐文件: ${fileName}`)
            } else {
              console.error(`音乐生成失败 ${storyboard.stage_id}:`, await musicResponse.text())
            }
          } catch (error) {
            console.error(`音乐生成失败 ${storyboard.stage_id}:`, error)
          }
        }
      }

      // 生成并下载ZIP文件
      const content = await zip.generateAsync({ type: 'blob' })
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-')
      const fileName = `故事板_${storyData.story_title || '未命名'}_${timestamp}.zip`
      
      // 创建下载链接
      const url = URL.createObjectURL(content)
      const link = document.createElement('a')
      link.href = url
      link.download = fileName
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)

      console.log('✅ 故事板包下载完成')
    } catch (error) {
      console.error('下载失败:', error)
      alert('下载失败，请稍后重试')
    } finally {
      setIsDownloading(false)
    }
  }

  useEffect(() => {
    async function loadStoryboard() {
      try {
        // 从sessionStorage获取生成的数据
        const generatedData = sessionStorage.getItem('generatedStoryboardData')
        
        if (!generatedData) {
          throw new Error('没有找到故事板数据，请先生成游戏内容')
        }
        
        console.log('📊 使用生成的故事板数据')
        const parsedStoryData: StoryData = JSON.parse(generatedData)
        setStoryData(parsedStoryData)
        
        const newNodes: Node[] = []
        const newEdges: Edge[] = []
        
        parsedStoryData.storyboards.forEach((storyboard, index) => {
          const nodeData = {
            sceneName: storyboard.stage_name,
            stageId: storyboard.stage_id,
            characters: storyboard.storyboard.人物档案,
            dialogue: storyboard.storyboard.人物对话,
            script: storyboard.storyboard.剧本,
            imagePrompt: storyboard.storyboard.图片提示词 || '',
            sceneInfo: storyboard.storyboard.分镜基础信息,
            teachingGoal: storyboard.teachingGoal,
            subject: parsedStoryData.subject,
            grade: parsedStoryData.grade,
            // 新增：预生成的内容
            preGeneratedImageUrl: storyboard.generated_image_url,
            preGeneratedDialogue: storyboard.generated_dialogue,
            generationStatus: storyboard.generation_status,
          }

          newNodes.push({
            id: storyboard.stage_id,
            type: 'storyboard',
            position: { 
              x: (index % 3) * 350, 
              y: Math.floor(index / 3) * 300 
            },
            data: nodeData,
          })

          if (storyboard.storyboard.人物对话?.场景转换) {
            Object.entries(storyboard.storyboard.人物对话.场景转换).forEach(([targetId, description]) => {
              newEdges.push({
                id: `${storyboard.stage_id}-${targetId}`,
                source: storyboard.stage_id,
                target: targetId,
                label: String(description),
                style: { stroke: '#8b5cf6' },
                labelStyle: { fill: '#8b5cf6', fontWeight: 600 },
              })
            })
          }
        })

        setNodes(newNodes)
        setEdges(newEdges)
      } catch (error) {
        console.error('Failed to load storyboard data:', error)
        // 可以设置一个错误状态来显示给用户
        alert(`加载故事板数据失败: ${error instanceof Error ? error.message : '未知错误'}`)
      } finally {
        setIsLoading(false)
      }
    }

    loadStoryboard()
  }, [setNodes, setEdges])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
          <div className="text-lg text-white">加载故事板数据中...</div>
          <div className="text-sm text-gray-300 mt-2">正在构建ReactFlow节点图...</div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ width: '100vw', height: '100vh' }} className="relative">
      {/* 顶部按钮组 */}
      <div className="absolute top-4 left-4 z-10 flex gap-3">
        <Link 
          href="/"
          className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-semibold shadow-lg"
        >
          ← 返回首页
        </Link>
        <button
          onClick={downloadStoryboardPackage}
          disabled={isDownloading || !storyData}
          className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-colors font-semibold shadow-lg flex items-center gap-2"
        >
          {isDownloading ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              打包中...
            </>
          ) : (
            <>
              📦 下载故事板包
            </>
          )}
        </button>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        nodeTypes={nodeTypes}
        fitView
        zoomOnScroll={true}
        zoomOnPinch={true}
        panOnScroll={false}
        zoomOnDoubleClick={true}
        minZoom={0.1}
        maxZoom={4}
      >
        <Controls />
        <Background color="#aaa" gap={16} />
      </ReactFlow>
    </div>
  )
}