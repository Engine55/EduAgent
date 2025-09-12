'use client'

import { useCallback, useEffect, useState } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Connection,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
} from 'reactflow'
import 'reactflow/dist/style.css'
import CustomStoryboardNode from '@/components/CustomStoryboardNode'

const nodeTypes = {
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
  storyboards: Array<{
    stage_index: number
    stage_name: string
    stage_id: string
    storyboard: StoryboardData
  }>
}

export default function Home() {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [isLoading, setIsLoading] = useState(true)

  const onConnect = useCallback(
    (params: Edge | Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges],
  )

  useEffect(() => {
    async function loadStoryboard() {
      try {
        const response = await fetch('/storyboards_story_09965411_20250912_051931.json')
        const storyData: StoryData = await response.json()
        
        const newNodes: Node[] = []
        const newEdges: Edge[] = []
        
        storyData.storyboards.forEach((storyboard, index) => {
          const nodeData = {
            sceneName: storyboard.stage_name,
            characters: storyboard.storyboard.人物档案,
            dialogue: storyboard.storyboard.人物对话,
            script: storyboard.storyboard.剧本,
            imagePrompt: storyboard.storyboard.图片提示词 || '',
            sceneInfo: storyboard.storyboard.分镜基础信息,
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
                label: description,
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
      } finally {
        setIsLoading(false)
      }
    }

    loadStoryboard()
  }, [setNodes, setEdges])

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-lg">加载故事板数据中...</div>
      </div>
    )
  }

  return (
    <div style={{ width: '100vw', height: '100vh' }}>
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
        defaultZoom={1}
      >
        <Controls />
        <Background color="#aaa" gap={16} />
      </ReactFlow>
    </div>
  )
}