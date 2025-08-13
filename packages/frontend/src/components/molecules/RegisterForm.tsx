import React, { useState } from 'react'
import { Button } from '../atoms/button'
import { Input } from '../atoms/input'
import { Label } from '../atoms/label'
import { Card } from '../atoms/card'
import { useToast } from '../atoms/use-toast'
import { Loader2, Mail, Lock, User, CheckCircle, AlertCircle } from 'lucide-react'
import { apiClient } from '../../api/client'
import { useNavigate } from 'react-router-dom'

export const RegisterForm: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    fullName: ''
  })
  const [isLoading, setIsLoading] = useState(false)
  const [registerStatus, setRegisterStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const { toast } = useToast()
  const navigate = useNavigate()

  const validateForm = () => {
    if (!formData.email || !formData.password || !formData.fullName) {
      toast({
        title: '入力エラー',
        description: 'すべての必須項目を入力してください',
        variant: 'destructive',
        duration: 3000
      })
      return false
    }

    if (formData.password !== formData.confirmPassword) {
      toast({
        title: 'パスワードエラー',
        description: 'パスワードが一致しません',
        variant: 'destructive',
        duration: 3000
      })
      return false
    }

    if (formData.password.length < 8) {
      toast({
        title: 'パスワードエラー',
        description: 'パスワードは8文字以上で入力してください',
        variant: 'destructive',
        duration: 3000
      })
      return false
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!validateForm()) {
      return
    }

    setIsLoading(true)
    setRegisterStatus('loading')

    try {
      await apiClient.post('/api/v1/auth/register', {
        email: formData.email,
        password: formData.password,
        full_name: formData.fullName
      })
      
      setRegisterStatus('success')
      
      toast({
        title: '登録が完了しました',
        description: (
          <div className="space-y-2">
            <p>確認メールを送信しました。</p>
            <p className="text-sm">メール内のリンクをクリックして本登録を完了してください。</p>
          </div>
        ),
        duration: 10000
      })

      // Clear form
      setFormData({
        email: '',
        password: '',
        confirmPassword: '',
        fullName: ''
      })

      // Redirect to login after delay
      setTimeout(() => {
        navigate('/login')
      }, 3000)
      
    } catch (error: any) {
      setRegisterStatus('error')
      setIsLoading(false)
      
      let errorMessage = '登録に失敗しました'
      
      if (error.response?.status === 409) {
        errorMessage = 'このメールアドレスは既に登録されています'
      } else if (error.response?.status === 400) {
        errorMessage = error.response.data.detail || '入力内容に誤りがあります'
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail
      }
      
      toast({
        title: '登録エラー',
        description: errorMessage,
        variant: 'destructive',
        duration: 5000
      })

      setTimeout(() => setRegisterStatus('idle'), 2000)
    }
  }

  const getButtonContent = () => {
    switch (registerStatus) {
      case 'loading':
        return (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            登録処理中...
          </>
        )
      case 'success':
        return (
          <>
            <CheckCircle className="mr-2 h-4 w-4 text-green-600" />
            登録完了
          </>
        )
      default:
        return 'アカウント作成'
    }
  }

  return (
    <Card className="w-full max-w-md mx-auto p-6">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold">新規登録</h2>
          <p className="text-sm text-gray-600 mt-2">
            PMO Agentアカウントを作成します
          </p>
        </div>

        {registerStatus === 'success' && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
            <div className="flex items-start">
              <AlertCircle className="h-5 w-5 text-green-600 mt-0.5" />
              <div className="ml-3">
                <p className="text-sm text-green-800">
                  確認メールを送信しました。メールをご確認ください。
                </p>
              </div>
            </div>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="fullName">お名前 *</Label>
          <div className="relative">
            <User className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="fullName"
              type="text"
              placeholder="山田 太郎"
              value={formData.fullName}
              onChange={(e) => setFormData({ ...formData, fullName: e.target.value })}
              disabled={isLoading}
              className="pl-10"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">メールアドレス *</Label>
          <div className="relative">
            <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="email"
              type="email"
              placeholder="your@email.com"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              disabled={isLoading}
              className="pl-10"
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="password">パスワード * (8文字以上)</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="password"
              type="password"
              placeholder="••••••••"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              disabled={isLoading}
              className="pl-10"
              minLength={8}
              required
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="confirmPassword">パスワード（確認） *</Label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              id="confirmPassword"
              type="password"
              placeholder="••••••••"
              value={formData.confirmPassword}
              onChange={(e) => setFormData({ ...formData, confirmPassword: e.target.value })}
              disabled={isLoading}
              className="pl-10"
              required
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={isLoading || registerStatus === 'success'}
          className="w-full transition-all duration-300"
          variant={registerStatus === 'error' ? 'destructive' : 'default'}
        >
          {getButtonContent()}
        </Button>

        <div className="text-center text-sm pt-4">
          <p className="text-gray-600">
            既にアカウントをお持ちの方は
            <a href="/login" className="text-blue-600 hover:underline ml-1">
              ログイン
            </a>
          </p>
        </div>
      </form>
    </Card>
  )
}