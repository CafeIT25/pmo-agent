import React from 'react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from './dialog'
import { Button } from './button'
import { AlertCircle, XCircle } from 'lucide-react'

interface ErrorModalProps {
  isOpen: boolean
  onClose: () => void
  title: string
  description: string
  errorType?: 'insufficient_credits' | 'rate_limit' | 'general'
  actionLabel?: string
  onAction?: () => void
}

export const ErrorModal: React.FC<ErrorModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  errorType = 'general',
  actionLabel = '閉じる',
  onAction
}) => {
  const getIcon = () => {
    switch (errorType) {
      case 'insufficient_credits':
        return <XCircle className="h-6 w-6 text-red-600" />
      case 'rate_limit':
        return <AlertCircle className="h-6 w-6 text-yellow-600" />
      default:
        return <AlertCircle className="h-6 w-6 text-red-600" />
    }
  }

  const getBackgroundColor = () => {
    switch (errorType) {
      case 'insufficient_credits':
        return 'bg-red-50'
      case 'rate_limit':
        return 'bg-yellow-50'
      default:
        return 'bg-red-50'
    }
  }

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <div className={`flex items-center gap-3 p-3 rounded-lg ${getBackgroundColor()}`}>
            {getIcon()}
            <DialogTitle className="text-lg font-semibold">
              {title}
            </DialogTitle>
          </div>
        </DialogHeader>
        
        <DialogDescription className="py-4 text-sm text-gray-600">
          {description}
          
          {errorType === 'insufficient_credits' && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="font-semibold mb-2">対処方法:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>管理者にOpenAI APIクレジットの補充を依頼してください</li>
                <li>OpenAI ダッシュボードで使用状況を確認してください</li>
                <li>月間制限額の引き上げを検討してください</li>
              </ul>
            </div>
          )}
          
          {errorType === 'rate_limit' && (
            <div className="mt-4 p-3 bg-gray-50 rounded-lg">
              <p className="font-semibold mb-2">対処方法:</p>
              <ul className="list-disc list-inside space-y-1 text-xs">
                <li>数分待ってから再試行してください</li>
                <li>同時実行するAI処理を減らしてください</li>
                <li>必要に応じてAPIプランのアップグレードを検討してください</li>
              </ul>
            </div>
          )}
        </DialogDescription>
        
        <DialogFooter className="flex gap-2">
          {onAction && errorType === 'insufficient_credits' && (
            <Button
              variant="outline"
              onClick={() => {
                window.open('https://platform.openai.com/usage', '_blank')
                onAction()
              }}
            >
              使用状況を確認
            </Button>
          )}
          <Button onClick={onClose}>
            {actionLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}