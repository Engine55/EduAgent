'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'

interface HistoryItem {
  story_id: string
  requirement_id: string
  story_title: string
  subject: string
  grade: string
  created_at: string
  updated_at: string
  storyboard_count: number
}

export default function HistoryPage() {
  const [historyData, setHistoryData] = useState<HistoryItem[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    async function fetchHistory() {
      try {
        const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/get_all_stories`)
        const result = await response.json()
        
        if (result.success) {
          setHistoryData(result.data || [])
        } else {
          setError(result.message || '获取历史记录失败')
        }
      } catch (err) {
        setError('网络请求失败')
        console.error('获取历史记录失败:', err)
      } finally {
        setIsLoading(false)
      }
    }

    fetchHistory()
  }, [])

  const handleViewStoryboard = async (item: HistoryItem) => {
    try {
      // 获取完整的故事数据
      const response = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_API_URL}/get_story_by_id`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          story_id: item.story_id
        }),
      })

      const result = await response.json()
      
      if (result.success && result.data.storyboards_data) {
        // 调试：检查数据结构
        console.log('获取到的完整数据:', result.data)
        console.log('storyboards_data:', result.data.storyboards_data)
        console.log('storyboards数组:', result.data.storyboards_data.storyboards)
        
        // 将数据存储到sessionStorage
        const storyboardPageData = {
          story_id: item.story_id,
          story_title: item.story_title,
          subject: item.subject,
          grade: item.grade,
          storyboards: result.data.storyboards_data.storyboards || []
        }
        
        console.log('传递给storyboard页面的数据:', storyboardPageData)
        
        sessionStorage.setItem('generatedStoryboardData', JSON.stringify(storyboardPageData))
        
        // 跳转到故事板页面
        router.push('/storyboard')
      } else {
        alert('获取故事数据失败')
      }
    } catch (error) {
      console.error('获取故事数据失败:', error)
      alert('获取故事数据失败')
    }
  }

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleString('zh-CN')
    } catch {
      return dateStr
    }
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-white mx-auto mb-4"></div>
          <div className="text-lg text-white">加载历史记录中...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900 flex items-center justify-center">
        <div className="text-center">
          <div className="text-lg text-red-300 mb-4">错误: {error}</div>
          <Link href="/" className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg">
            返回首页
          </Link>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-900 via-blue-900 to-indigo-900">
      {/* 头部导航 */}
      <header className="bg-black bg-opacity-30 backdrop-blur-sm border-b border-purple-500/30 p-4">
        <div className="max-w-6xl mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold text-white">历史记录</h1>
          <Link 
            href="/" 
            className="px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
          >
            返回首页
          </Link>
        </div>
      </header>

      {/* 内容区域 */}
      <div className="max-w-6xl mx-auto p-6">
        {historyData.length === 0 ? (
          <div className="text-center py-12">
            <div className="text-gray-300 text-lg mb-4">暂无历史记录</div>
            <Link 
              href="/" 
              className="px-6 py-3 bg-purple-600 hover:bg-purple-700 text-white rounded-lg transition-colors"
            >
              开始创建游戏
            </Link>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {historyData.map((item) => (
              <div
                key={item.story_id}
                className="bg-white bg-opacity-10 backdrop-blur-sm rounded-lg p-6 border border-purple-500/30 hover:bg-opacity-15 transition-all duration-200"
              >
                <div className="mb-4">
                  <h3 className="text-xl font-bold text-white mb-2 truncate" title={item.story_title}>
                    {item.story_title || '未命名游戏'}
                  </h3>
                  <div className="space-y-1 text-sm">
                    <div className="text-purple-300">
                      <span className="font-medium">学科:</span> {item.subject || '未知'}
                    </div>
                    <div className="text-purple-300">
                      <span className="font-medium">年级:</span> {item.grade || '未知'}
                    </div>
                    <div className="text-purple-300">
                      <span className="font-medium">关卡数:</span> {item.storyboard_count || 0}
                    </div>
                  </div>
                </div>
                
                <div className="mb-4 text-xs text-gray-400">
                  <div>创建时间: {formatDate(item.created_at)}</div>
                  <div>更新时间: {formatDate(item.updated_at)}</div>
                </div>

                <div className="flex gap-2">
                  <button
                    onClick={() => handleViewStoryboard(item)}
                    className="flex-1 px-4 py-2 bg-green-600 hover:bg-green-700 text-white rounded-lg transition-colors text-sm font-medium"
                  >
                    查看故事板
                  </button>
                  <div className="text-xs text-gray-400 self-center px-2">
                    {item.story_id.replace('story_', '')}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}