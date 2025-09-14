'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
  analysis_report?: string  // 添加分析报告字段
  story_framework?: string  // 添加故事框架字段
}

interface ConversationStage {
  stage: string
  ready_for_stage2: boolean
  requirement_id?: string
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isInitialized, setIsInitialized] = useState(false)
  const [conversationStage, setConversationStage] = useState<ConversationStage>({
    stage: 'not_started',
    ready_for_stage2: false
  })
  const [storyboardData, setStoryboardData] = useState<any>(null)
  const [isGenerating, setIsGenerating] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const router = useRouter()

  // 下载分析报告
  const handleDownloadReport = (report: string, messageId: string) => {
    const blob = new Blob([report], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `RPG教育游戏需求分析报告_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // 下载故事框架
  const handleDownloadStoryFramework = (storyFramework: string, messageId: string) => {
    const blob = new Blob([storyFramework], { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `RPG教育游戏故事框架_${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
  }

  // 初始化对话
  useEffect(() => {
    const initializeConversation = async () => {
      if (isInitialized) return // 防止重复初始化
      
      setIsInitialized(true) // 立即设置为true，防止重复调用
      
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/start_conversation`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({}),
        })

        const result = await response.json()
        console.log('start_conversation响应:', result)
        
        if (result.success) {
          const aiMessage: Message = {
            id: '1',
            type: 'ai',
            content: result.data.message,
            timestamp: new Date()
          }
          setMessages([aiMessage])
          setConversationStage({
            stage: 'collecting',
            ready_for_stage2: false
          })
        }
      } catch (error) {
        console.error('初始化对话失败:', error)
        const errorMessage: Message = {
          id: '1',
          type: 'ai',
          content: '抱歉，初始化对话时出现了问题。请刷新页面重试。',
          timestamp: new Date()
        }
        setMessages([errorMessage])
      }
    }

    initializeConversation()
  }, [isInitialized])

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return

    const userMessage: Message = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)

    try {
      // 调用后端process_request接口
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/process_request`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_input: userMessage.content
        }),
      })

      const result = await response.json()
      
      if (result.success) {
        console.log('Backend response:', result.data) // 调试信息
        console.log('Analysis report:', result.data.analysis_report) // 调试信息
        
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'ai',
          content: result.data.response || '收到您的消息了！',
          timestamp: new Date(),
          analysis_report: result.data.analysis_report,  // 添加分析报告
          story_framework: result.data.story_framework   // 添加故事框架
        }

        setMessages(prev => [...prev, aiMessage])
        
        // 更新对话阶段状态
        if (result.data.ready_for_stage2) {
          setConversationStage({
            stage: 'stage1_complete',
            ready_for_stage2: true,
            requirement_id: result.data.requirement_id
          })
        }
      } else {
        throw new Error(result.error || '请求失败')
      }
    } catch (error) {
      console.error('发送消息失败:', error)
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: '抱歉，发送消息时出现了问题，请稍后重试。',
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  const handleGenerateStoryboards = async () => {
    if (!conversationStage.requirement_id || isGenerating) return

    setIsGenerating(true)
    
    try {
      console.log('🎬 开始生成游戏场景，需求ID:', conversationStage.requirement_id)
      
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/generate_complete_storyboards`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          requirement_id: conversationStage.requirement_id
        }),
      })

      const result = await response.json()
      
      if (result.success) {
        console.log('✅ 故事板生成成功:', result.data)
        setStoryboardData(result.data)
        
        // 添加一条成功消息到对话中
        const successMessage: Message = {
          id: (Date.now()).toString(),
          type: 'ai',
          content: `🎉 游戏内容生成完成！\n\n✅ RPG故事框架：${result.data.rpg_framework?.标题 || '未知标题'}\n✅ 生成关卡数：${result.data.total_stages}个\n✅ 故事板数：${result.data.successful_storyboards}个\n\n准备跳转到故事板可视化页面...`,
          timestamp: new Date()
        }
        setMessages(prev => [...prev, successMessage])

        // 将数据存储到sessionStorage，然后跳转到故事板页面
        // 优化：只存储图片URL，移除大体积的base64数据
        const optimizedStoryboards = (result.data.storyboards_list || []).map((storyboard: any) => ({
          ...storyboard,
          // 保留图片URL，移除base64数据以节省空间
          generated_image_url: storyboard.generated_image_data?.original_url || null,
          generated_image_data: undefined // 移除base64数据
        }))

        const storyboardPageData = {
          story_id: result.data.requirement_id,
          story_title: result.data.rpg_framework?.标题 || '未知故事',
          storyboards: optimizedStoryboards
        }
        
        sessionStorage.setItem('generatedStoryboardData', JSON.stringify(storyboardPageData))
        
        // 延迟1秒后跳转，让用户看到成功消息
        setTimeout(() => {
          router.push('/storyboard')
        }, 1500)
      } else {
        throw new Error(result.error || '生成失败')
      }
    } catch (error) {
      console.error('❌ 生成故事板失败:', error)
      const errorMessage: Message = {
        id: (Date.now()).toString(),
        type: 'ai',
        content: `❌ 游戏内容生成失败：${error instanceof Error ? error.message : '未知错误'}。请稍后重试。`,
        timestamp: new Date()
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsGenerating(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex flex-col">
      {/* 头部导航 */}
      <header className="bg-black bg-opacity-30 backdrop-blur-sm border-b border-purple-500/30 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white">🎮 RPG教育游戏生成器</h1>
          <div className="flex gap-4">
            <Link 
              href="/history" 
              className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
            >
              历史记录
            </Link>
            <Link 
              href="/storyboard" 
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              查看故事板
            </Link>
{conversationStage.ready_for_stage2 && (
              <Link 
                href="/storyboard" 
                className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors"
              >
                查看已生成故事板
              </Link>
            )}
          </div>
        </div>
      </header>

      {/* 对话区域 */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-4">
        {/* 消息列表 */}
        <div className="flex-1 overflow-y-auto mb-4 space-y-4">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-xs md:max-w-md lg:max-w-lg xl:max-w-xl px-4 py-3 rounded-lg ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none'
                    : 'bg-white bg-opacity-90 text-gray-800 rounded-bl-none shadow-lg'
                }`}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                
                {/* 下载按钮区域 */}
                {(message.analysis_report || message.story_framework) && (
                  <div className="mt-3 pt-3 border-t border-gray-300 space-y-2">
                    {/* 分析报告下载按钮 */}
                    {message.analysis_report && (
                      <button
                        onClick={() => handleDownloadReport(message.analysis_report!, message.id)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white text-sm rounded-md transition-colors mr-2"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        下载需求分析报告
                      </button>
                    )}
                    {/* 故事框架下载按钮 */}
                    {message.story_framework && (
                      <button
                        onClick={() => handleDownloadStoryFramework(message.story_framework!, message.id)}
                        className="inline-flex items-center gap-2 px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white text-sm rounded-md transition-colors"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3a2 2 0 012-2h4a2 2 0 012 2v4m-6 0V6a2 2 0 012-2h4a2 2 0 012 2v1m-6 0h8m-8 0l-.5 5a2 2 0 002 2h5a2 2 0 002-2L16 7m-8 0V5a2 2 0 012-2h4a2 2 0 012 2v2"/>
                        </svg>
                        下载故事框架
                      </button>
                    )}
                  </div>
                )}
                
                <div className={`text-xs mt-2 ${
                  message.type === 'user' ? 'text-blue-200' : 'text-gray-500'
                }`}>
                  {message.timestamp.toLocaleTimeString()}
                </div>
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white bg-opacity-90 text-gray-800 rounded-lg rounded-bl-none shadow-lg px-4 py-3">
                <div className="flex items-center space-x-2">
                  <div className="animate-pulse">AI正在思考中</div>
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* 输入区域 */}
        <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-4 border border-purple-500/30">
          {conversationStage.stage === 'stage1_complete' ? (
            // Stage1完成后显示生成按钮
            <div className="text-center space-y-4">
              <div className="p-3 bg-green-500 bg-opacity-20 border border-green-400 rounded-lg">
                <p className="text-green-200 text-sm">
                  ✅ 信息收集完成！需求ID: {conversationStage.requirement_id}
                </p>
                <p className="text-green-300 text-xs mt-1">对话已结束，您可以开始生成游戏场景</p>
              </div>
              <button 
                className="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 disabled:from-gray-500 disabled:to-gray-600 text-white rounded-lg transition-all font-bold text-lg shadow-lg transform hover:scale-105 disabled:transform-none disabled:cursor-not-allowed"
                onClick={handleGenerateStoryboards}
                disabled={isGenerating || !conversationStage.requirement_id}
              >
                {isGenerating ? '🎬 正在生成中...' : '🎮 Generate Game Scene'}
              </button>
            </div>
          ) : (
            // Stage1进行中显示输入框
            <div className="flex space-x-4">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyPress={handleKeyPress}
                placeholder="请输入您的需求..."
                className="flex-1 bg-white bg-opacity-20 text-white placeholder-gray-300 rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500 resize-none"
                rows={2}
                disabled={isLoading}
              />
              <button
                onClick={handleSendMessage}
                disabled={isLoading || !inputValue.trim()}
                className="px-6 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-500 text-white rounded-lg transition-colors font-semibold"
              >
                发送
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 简单的状态显示区域 */}
      {storyboardData && (
        <div className="max-w-4xl mx-auto w-full p-4 mt-6">
          <div className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-4 border border-purple-500/30 text-center">
            <h2 className="text-lg font-bold text-white mb-2">
              🎉 游戏内容生成完成！
            </h2>
            <p className="text-green-300 text-sm mb-4">
              ✅ {storyboardData.rpg_framework?.标题 || '未知标题'} - {storyboardData.total_stages}个关卡 - {storyboardData.successful_storyboards}个故事板
            </p>
            <Link
              href="/storyboard"
              className="inline-block px-6 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors font-semibold"
            >
              🎬 查看ReactFlow故事板可视化
            </Link>
          </div>
        </div>
      )}
    </div>
  )
}