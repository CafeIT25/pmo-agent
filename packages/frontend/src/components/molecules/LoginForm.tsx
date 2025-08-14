import React, { useState } from 'react'
import { Button } from '../atoms/button'
import { Input } from '../atoms/input'
import { Label } from '../atoms/label'
import { Card } from '../atoms/card'
import { useToast } from '../atoms/use-toast'
import { Loader2, Mail, Lock, CheckCircle } from 'lucide-react'
import { useAuthStore } from '../../store/authStore'
import { useNavigate } from 'react-router-dom'
import { isMockMode } from '../../api/mockClient'

export const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loginStatus, setLoginStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const { toast } = useToast()
  const navigate = useNavigate()
  const login = useAuthStore((state) => state.login)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    // Validate inputs
    if (!email || !password) {
      toast({
        title: '入力エラー',
        description: 'メールアドレスとパスワードを入力してください',
        variant: 'destructive',
        duration: 3000
      })
      return
    }

    setIsLoading(true)
    setLoginStatus('loading')

    try {
      await login(email, password)
      
      setLoginStatus('success')
      
      toast({
        title: 'ログインに成功しました',
        description: 'ダッシュボードにリダイレクトしています...',
        duration: 2000
      })

      // Redirect after short delay to show success message
      setTimeout(() => {
        navigate('/dashboard')
      }, 1000)
      
    } catch (error: any) {
      setLoginStatus('error')
      setIsLoading(false)
      
      let errorMessage = 'ログインに失敗しました'
      
      if (error.response?.status === 401) {
        errorMessage = 'メールアドレスまたはパスワードが正しくありません'
      } else if (error.response?.status === 423) {
        errorMessage = 'アカウントがロックされています。30分後に再度お試しください'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      
      toast({
        title: 'ログインエラー',
        description: errorMessage,
        variant: 'destructive',
        duration: 5000
      })

      // Reset status after error
      setTimeout(() => setLoginStatus('idle'), 2000)
    }
  }

  const getButtonContent = () => {
    switch (loginStatus) {
      case 'loading':
        return (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ログイン中...
          </>
        )
      case 'success':
        return (
          <>
            <CheckCircle className="mr-2 h-4 w-4 text-green-600" />
            ログイン成功
          </>
        )
      default:
        return 'ログイン'
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">メールアドレス</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              className="pl-10"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">パスワード</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              className="pl-10"
              required
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={isLoading}
          className="w-full transition-all duration-300"
          variant={loginStatus === 'error' ? 'destructive' : 'default'}
        >
          {getButtonContent()}
        </Button>

        <div className="text-center space-y-2 pt-4">
          <div className="text-sm text-gray-600">
            または
          </div>
          <div className="space-y-2">
            <Button
              type="button"
              variant="outline"
              className="w-full"
              disabled={isLoading}
              onClick={() => {
                toast({
                  title: 'Google認証',
                  description: 'Google認証ページにリダイレクトします...',
                  duration: 2000
                })
                window.location.href = `/api/v1/oauth/google/authorize?redirect_uri=${encodeURIComponent(window.location.origin + '/auth/callback')}`
              }}
            >
              <img src="/google-logo.svg" alt="Google" className="w-4 h-4 mr-2" />
              Googleでログイン
            </Button>
            
            <Button
              type="button"
              variant="outline"
              className="w-full"
              disabled={isLoading}
              onClick={() => {
                toast({
                  title: 'Microsoft認証',
                  description: 'Microsoft認証ページにリダイレクトします...',
                  duration: 2000
                })
                window.location.href = `/api/v1/oauth/microsoft/authorize?redirect_uri=${encodeURIComponent(window.location.origin + '/auth/callback')}`
              }}
            >
              <img src="/microsoft-logo.svg" alt="Microsoft" className="w-4 h-4 mr-2" />
              Microsoftでログイン
            </Button>
          </div>
        </div>

        {/* テストユーザー情報 - 常に表示 */}
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="text-sm font-medium text-blue-800 mb-2">
            🧪 テストアカウント {isMockMode && '(モックモード有効)'}
          </h3>
          <div className="space-y-2 text-xs text-blue-700">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <strong>一般ユーザー:</strong><br />
                test@example.com<br />
                testpass123
              </div>
              <div>
                <strong>管理者:</strong><br />
                admin@example.com<br />
                adminpass123
              </div>
            </div>
            <div className="mt-2">
              <strong>デモユーザー:</strong><br />
              demo@example.com / demopass123
            </div>
          </div>
          <div className="mt-3 space-y-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-full text-xs"
              onClick={() => {
                setEmail('test@example.com')
                setPassword('testpass123')
              }}
              disabled={isLoading}
            >
              一般ユーザーでログイン
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-full text-xs"
              onClick={() => {
                setEmail('demo@example.com')
                setPassword('demopass123')
              }}
              disabled={isLoading}
            >
              デモユーザーでログイン
            </Button>
          </div>
        </div>

        <div className="text-center text-sm">
          <a href="/register" className="text-blue-600 hover:underline">
            アカウントをお持ちでない方はこちら
          </a>
        </div>
      </form>
    </Card>
  )
}