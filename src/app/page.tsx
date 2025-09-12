'use client'

import { useState, useRef, useEffect } from 'react'
import Link from 'next/link'

interface Message {
  id: string
  type: 'user' | 'ai'
  content: string
  timestamp: Date
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
  const messagesEndRef = useRef<HTMLDivElement>(null)

  // 初始化对话
  useEffect(() => {
    const initializeConversation = async () => {
      if (isInitialized) return // 防止重复初始化
      
      setIsInitialized(true) // 立即设置为true，防止重复调用
      
      try {
        const response = await fetch('http://localhost:8000/start_conversation', {
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
  }, [])

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
      const response = await fetch('http://localhost:8000/process_request', {
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
        const aiMessage: Message = {
          id: (Date.now() + 1).toString(),
          type: 'ai',
          content: result.data.response || '收到您的消息了！',
          timestamp: new Date()
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex flex-col">
      {/* 头部导航 */}
      <header className="bg-black bg-opacity-30 backdrop-blur-sm border-b border-purple-500/30 p-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white">🎮 RPG教育游戏生成器</h1>
          <div className="flex gap-4">
            <Link 
              href="/storyboard" 
              className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              查看故事板
            </Link>
            {conversationStage.ready_for_stage2 && (
              <button className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors">
                生成故事板
              </button>
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
                className="px-8 py-3 bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700 text-white rounded-lg transition-all font-bold text-lg shadow-lg transform hover:scale-105"
                onClick={() => {
                  // TODO: 实现生成游戏场景逻辑
                  console.log('生成游戏场景', conversationStage.requirement_id)
                }}
              >
                🎮 Generate Game Scene
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
    </div>
  )
}