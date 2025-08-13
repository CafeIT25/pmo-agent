import React, { useState } from 'react'
import { Button } from '../atoms/button'
import { useToast } from '../atoms/use-toast'
import { Loader2, Brain, CheckCircle, XCircle } from 'lucide-react'
import { apiClient } from '../../api/client'

interface AITaskSupportButtonProps {
  taskId: string
  context?: string
  onSupportGenerated?: (supportData: any) => void
}

export const AITaskSupportButton: React.FC<AITaskSupportButtonProps> = ({
  taskId,
  context = '',
  onSupportGenerated
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [supportStatus, setSupportStatus] = useState<'idle' | 'generating' | 'success' | 'error'>('idle')
  const { toast } = useToast()

  const handleAISupport = async () => {
    setIsLoading(true)
    setSupportStatus('generating')

    // Show initial toast
    const loadingToastId = toast({
      title: 'AI分析を開始しています',
      description: (
        <div className="flex items-center">
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          <span>タスクを分析中...</span>
        </div>
      ),
      duration: 0 // Keep showing
    })

    try {
      // Request AI support
      const response = await apiClient.post('/api/v1/ai/task-suggestions', {
        task_id: taskId,
        context: context
      })

      const jobId = response.data.job_id
      let elapsedTime = 0
      const maxWaitTime = 30000 // 30 seconds as per requirements

      // Poll for job status
      const pollInterval = setInterval(async () => {
        try {
          elapsedTime += 2000

          // Update toast with elapsed time
          if (elapsedTime > 10000) {
            toast({
              title: 'AI分析を実行中',
              description: `処理に時間がかかっています... (${Math.floor(elapsedTime / 1000)}秒経過)`,
              duration: 0
            })
          }

          const statusResponse = await apiClient.get(`/api/v1/ai/job/${jobId}`)
          const status = statusResponse.data

          if (status.status === 'completed') {
            clearInterval(pollInterval)
            setSupportStatus('success')
            setIsLoading(false)
            
            toast({
              title: 'AI分析が完了しました',
              description: '提案内容が生成されました',
              duration: 5000
            })

            // Reset status after animation
            setTimeout(() => setSupportStatus('idle'), 2000)
            
            if (onSupportGenerated && status.result) {
              onSupportGenerated(status.result)
            }
          } else if (status.status === 'failed') {
            clearInterval(pollInterval)
            setSupportStatus('error')
            setIsLoading(false)
            
            toast({
              title: 'AI分析に失敗しました',
              description: status.error || 'エラーが発生しました',
              variant: 'destructive',
              duration: 5000
            })

            setTimeout(() => setSupportStatus('idle'), 2000)
          } else if (elapsedTime >= maxWaitTime) {
            // Show timeout warning
            toast({
              title: '処理に時間がかかっています',
              description: 'キャンセルするか、もう少しお待ちください',
              action: (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    clearInterval(pollInterval)
                    setIsLoading(false)
                    setSupportStatus('error')
                    setTimeout(() => setSupportStatus('idle'), 2000)
                  }}
                >
                  キャンセル
                </Button>
              ),
              duration: 0
            })
          }
        } catch (error) {
          clearInterval(pollInterval)
          setSupportStatus('error')
          setIsLoading(false)
          
          toast({
            title: 'ステータス確認エラー',
            description: 'AI分析の状態確認に失敗しました',
            variant: 'destructive',
            duration: 5000
          })

          setTimeout(() => setSupportStatus('idle'), 2000)
        }
      }, 2000)

    } catch (error: any) {
      setIsLoading(false)
      setSupportStatus('error')
      
      // クレジット不足エラーの処理
      if (error.response?.status === 402) {
        toast({
          title: '⚠️ OpenAI クレジット不足',
          description: error.response?.data?.detail?.message || 'OpenAI APIのクレジットが不足しています。管理者に連絡してください。',
          variant: 'destructive',
          duration: 10000
        })
      } 
      // レート制限エラーの処理
      else if (error.response?.status === 429) {
        toast({
          title: '⏱️ レート制限',
          description: error.response?.data?.detail?.message || 'OpenAI APIのレート制限に達しました。しばらく待ってから再試行してください。',
          variant: 'destructive',
          duration: 8000
        })
      }
      // その他のエラー
      else {
        toast({
          title: 'AI分析開始エラー',
          description: error.response?.data?.detail || 'AI分析の開始に失敗しました',
          variant: 'destructive',
          duration: 5000
        })
      }

      setTimeout(() => setSupportStatus('idle'), 2000)
    }
  }

  const getButtonContent = () => {
    switch (supportStatus) {
      case 'generating':
        return (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            AI分析中...
          </>
        )
      case 'success':
        return (
          <>
            <CheckCircle className="mr-2 h-4 w-4 text-green-600" />
            分析完了
          </>
        )
      case 'error':
        return (
          <>
            <XCircle className="mr-2 h-4 w-4 text-red-600" />
            分析失敗
          </>
        )
      default:
        return (
          <>
            <Brain className="mr-2 h-4 w-4" />
            AIでサポート
          </>
        )
    }
  }

  const getButtonVariant = () => {
    switch (supportStatus) {
      case 'success':
        return 'outline'
      case 'error':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  return (
    <Button
      onClick={handleAISupport}
      disabled={isLoading}
      variant={getButtonVariant()}
      className="transition-all duration-300"
    >
      {getButtonContent()}
    </Button>
  )
}