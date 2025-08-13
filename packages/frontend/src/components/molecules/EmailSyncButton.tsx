import React, { useState } from 'react'
import { Button } from '../atoms/button'
import { useToast } from '../atoms/use-toast'
import { Loader2, Mail, CheckCircle, XCircle } from 'lucide-react'
import { apiClient } from '../../api/client'

interface EmailSyncButtonProps {
  accountId: string
  onSyncComplete?: () => void
}

export const EmailSyncButton: React.FC<EmailSyncButtonProps> = ({
  accountId,
  onSyncComplete
}) => {
  const [isLoading, setIsLoading] = useState(false)
  const [syncStatus, setSyncStatus] = useState<'idle' | 'syncing' | 'success' | 'error'>('idle')
  const { toast } = useToast()

  const handleSync = async () => {
    setIsLoading(true)
    setSyncStatus('syncing')

    try {
      // Start email sync
      const response = await apiClient.post('/api/v1/email/sync', {
        account_id: accountId
      })

      const jobId = response.data.job_id

      // Show progress toast
      toast({
        title: 'メール同期を開始しました',
        description: '同期処理を実行中です...',
        duration: 0 // Keep showing until update
      })

      // Poll for job status
      const pollInterval = setInterval(async () => {
        try {
          const statusResponse = await apiClient.get(`/api/v1/email/sync/${jobId}`)
          const status = statusResponse.data

          if (status.status === 'completed') {
            clearInterval(pollInterval)
            setSyncStatus('success')
            setIsLoading(false)
            
            toast({
              title: 'メール同期が完了しました',
              description: `${status.processed_emails}件のメールを処理しました`,
              duration: 5000
            })

            // Reset status after animation
            setTimeout(() => setSyncStatus('idle'), 2000)
            
            if (onSyncComplete) {
              onSyncComplete()
            }
          } else if (status.status === 'failed') {
            clearInterval(pollInterval)
            setSyncStatus('error')
            setIsLoading(false)
            
            toast({
              title: 'メール同期に失敗しました',
              description: status.error_message || 'エラーが発生しました',
              variant: 'destructive',
              duration: 5000
            })

            // Reset status after animation
            setTimeout(() => setSyncStatus('idle'), 2000)
          }
        } catch (error) {
          clearInterval(pollInterval)
          setSyncStatus('error')
          setIsLoading(false)
          
          toast({
            title: 'ステータス確認エラー',
            description: '同期状態の確認に失敗しました',
            variant: 'destructive',
            duration: 5000
          })

          setTimeout(() => setSyncStatus('idle'), 2000)
        }
      }, 2000) // Poll every 2 seconds

      // Set timeout for long-running sync
      setTimeout(() => {
        if (isLoading) {
          clearInterval(pollInterval)
          setIsLoading(false)
          setSyncStatus('error')
          
          toast({
            title: 'タイムアウト',
            description: '同期処理がタイムアウトしました。後でもう一度お試しください。',
            variant: 'destructive',
            duration: 5000
          })

          setTimeout(() => setSyncStatus('idle'), 2000)
        }
      }, 300000) // 5 minutes timeout

    } catch (error: any) {
      setIsLoading(false)
      setSyncStatus('error')
      
      // クレジット不足エラーの処理
      if (error.response?.status === 402) {
        toast({
          title: '⚠️ OpenAI クレジット不足',
          description: error.response?.data?.detail?.message || 'OpenAI APIのクレジットが不足しています。メール分析にはAI機能が必要です。管理者に連絡してください。',
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
          title: '同期開始エラー',
          description: error.response?.data?.detail || 'メール同期の開始に失敗しました',
          variant: 'destructive',
          duration: 5000
        })
      }

      setTimeout(() => setSyncStatus('idle'), 2000)
    }
  }

  const getButtonContent = () => {
    switch (syncStatus) {
      case 'syncing':
        return (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            同期中...
          </>
        )
      case 'success':
        return (
          <>
            <CheckCircle className="mr-2 h-4 w-4 text-green-600" />
            同期完了
          </>
        )
      case 'error':
        return (
          <>
            <XCircle className="mr-2 h-4 w-4 text-red-600" />
            同期失敗
          </>
        )
      default:
        return (
          <>
            <Mail className="mr-2 h-4 w-4" />
            メール同期
          </>
        )
    }
  }

  const getButtonVariant = () => {
    switch (syncStatus) {
      case 'success':
        return 'outline'
      case 'error':
        return 'destructive'
      default:
        return 'default'
    }
  }

  return (
    <Button
      onClick={handleSync}
      disabled={isLoading}
      variant={getButtonVariant()}
      className="transition-all duration-300"
    >
      {getButtonContent()}
    </Button>
  )
}