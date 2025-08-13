import { useCallback } from 'react'
import { useToast } from '../components/atoms/use-toast'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/authStore'

interface ErrorHandlerOptions {
  defaultMessage?: string
  showToast?: boolean
  redirectOn401?: boolean
}

export const useErrorHandler = () => {
  const { toast } = useToast()
  const navigate = useNavigate()
  const logout = useAuthStore((state) => state.logout)

  const handleError = useCallback((
    error: any,
    options: ErrorHandlerOptions = {}
  ) => {
    const {
      defaultMessage = 'エラーが発生しました',
      showToast = true,
      redirectOn401 = true
    } = options

    console.error('Error occurred:', error)

    let errorMessage = defaultMessage
    let errorTitle = 'エラー'

    // Handle different error types
    if (error.response) {
      // Server responded with error
      const status = error.response.status
      const data = error.response.data

      switch (status) {
        case 400:
          errorTitle = '入力エラー'
          errorMessage = data.detail || '入力内容に誤りがあります'
          break
        case 401:
          errorTitle = '認証エラー'
          errorMessage = 'ログインが必要です'
          if (redirectOn401) {
            logout()
            navigate('/login')
          }
          break
        case 403:
          errorTitle = 'アクセス拒否'
          errorMessage = 'この操作を実行する権限がありません'
          break
        case 404:
          errorTitle = 'Not Found'
          errorMessage = '要求されたリソースが見つかりません'
          break
        case 409:
          errorTitle = '競合エラー'
          errorMessage = data.detail || 'リソースが既に存在します'
          break
        case 422:
          errorTitle = 'バリデーションエラー'
          errorMessage = data.detail || '入力値が正しくありません'
          break
        case 429:
          errorTitle = 'レート制限'
          errorMessage = 'リクエストが多すぎます。しばらく待ってから再度お試しください'
          break
        case 500:
          errorTitle = 'サーバーエラー'
          errorMessage = 'サーバーで問題が発生しました。しばらく待ってから再度お試しください'
          break
        case 503:
          errorTitle = 'メンテナンス中'
          errorMessage = 'サービスは現在メンテナンス中です'
          break
        default:
          if (data.detail) {
            errorMessage = data.detail
          }
      }
    } else if (error.request) {
      // Request made but no response
      errorTitle = 'ネットワークエラー'
      errorMessage = 'サーバーに接続できません。インターネット接続を確認してください'
    } else if (error.message) {
      // Something else happened
      errorMessage = error.message
    }

    if (showToast) {
      toast({
        title: errorTitle,
        description: errorMessage,
        variant: 'destructive',
        duration: 5000
      })
    }

    return {
      title: errorTitle,
      message: errorMessage,
      status: error.response?.status
    }
  }, [toast, navigate, logout])

  const handleAsyncOperation = useCallback(async <T,>(
    operation: () => Promise<T>,
    options: ErrorHandlerOptions = {}
  ): Promise<T | null> => {
    try {
      return await operation()
    } catch (error) {
      handleError(error, options)
      return null
    }
  }, [handleError])

  return {
    handleError,
    handleAsyncOperation
  }
}