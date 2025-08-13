import React, { useState } from 'react'
import { Button } from '../atoms/button'
import { useToast } from '../atoms/use-toast'
import { 
  Loader2, 
  Save, 
  Trash2, 
  CheckCircle, 
  XCircle,
  Edit,
  X
} from 'lucide-react'
import { apiClient } from '../../api/client'

interface TaskActionButtonsProps {
  taskId: string
  onUpdate?: () => void
  onDelete?: () => void
}

export const TaskSaveButton: React.FC<{
  taskId: string
  taskData: any
  onSave?: () => void
}> = ({ taskId, taskData, onSave }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [saveStatus, setSaveStatus] = useState<'idle' | 'saving' | 'success' | 'error'>('idle')
  const { toast } = useToast()

  const handleSave = async () => {
    setIsLoading(true)
    setSaveStatus('saving')

    try {
      await apiClient.put(`/api/v1/tasks/${taskId}`, taskData)
      
      setSaveStatus('success')
      setIsLoading(false)
      
      toast({
        title: 'タスクを保存しました',
        description: '変更が正常に保存されました',
        duration: 3000
      })

      setTimeout(() => setSaveStatus('idle'), 2000)
      
      if (onSave) {
        onSave()
      }
    } catch (error: any) {
      setSaveStatus('error')
      setIsLoading(false)
      
      toast({
        title: '保存に失敗しました',
        description: error.response?.data?.detail || 'タスクの保存中にエラーが発生しました',
        variant: 'destructive',
        duration: 5000
      })

      setTimeout(() => setSaveStatus('idle'), 2000)
    }
  }

  return (
    <Button
      onClick={handleSave}
      disabled={isLoading}
      variant={saveStatus === 'error' ? 'destructive' : 'default'}
      size="sm"
      className="transition-all duration-300"
    >
      {saveStatus === 'saving' && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {saveStatus === 'success' && <CheckCircle className="mr-2 h-4 w-4 text-green-600" />}
      {saveStatus === 'error' && <XCircle className="mr-2 h-4 w-4" />}
      {saveStatus === 'idle' && <Save className="mr-2 h-4 w-4" />}
      保存
    </Button>
  )
}

export const TaskDeleteButton: React.FC<{
  taskId: string
  onDelete?: () => void
}> = ({ taskId, onDelete }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [deleteStatus, setDeleteStatus] = useState<'idle' | 'deleting' | 'success' | 'error'>('idle')
  const [showConfirm, setShowConfirm] = useState(false)
  const { toast } = useToast()

  const handleDelete = async () => {
    setIsLoading(true)
    setDeleteStatus('deleting')

    try {
      await apiClient.delete(`/api/v1/tasks/${taskId}`)
      
      setDeleteStatus('success')
      setIsLoading(false)
      
      toast({
        title: 'タスクを削除しました',
        description: 'タスクが正常に削除されました',
        duration: 3000
      })

      if (onDelete) {
        onDelete()
      }
    } catch (error: any) {
      setDeleteStatus('error')
      setIsLoading(false)
      
      toast({
        title: '削除に失敗しました',
        description: error.response?.data?.detail || 'タスクの削除中にエラーが発生しました',
        variant: 'destructive',
        duration: 5000
      })

      setTimeout(() => setDeleteStatus('idle'), 2000)
    }
  }

  if (showConfirm) {
    return (
      <div className="flex gap-2">
        <Button
          onClick={handleDelete}
          disabled={isLoading}
          variant="destructive"
          size="sm"
        >
          {deleteStatus === 'deleting' ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="mr-2 h-4 w-4" />
          )}
          削除実行
        </Button>
        <Button
          onClick={() => setShowConfirm(false)}
          variant="outline"
          size="sm"
        >
          <X className="mr-2 h-4 w-4" />
          キャンセル
        </Button>
      </div>
    )
  }

  return (
    <Button
      onClick={() => setShowConfirm(true)}
      variant="outline"
      size="sm"
      className="text-red-600 hover:text-red-700"
    >
      <Trash2 className="mr-2 h-4 w-4" />
      削除
    </Button>
  )
}

export const TaskStatusButton: React.FC<{
  taskId: string
  currentStatus: string
  onStatusChange?: (newStatus: string) => void
}> = ({ taskId, currentStatus, onStatusChange }) => {
  const [isLoading, setIsLoading] = useState(false)
  const { toast } = useToast()

  const statusMap: { [key: string]: { label: string; next: string } } = {
    'pending': { label: '未着手', next: 'in_progress' },
    'in_progress': { label: '進行中', next: 'completed' },
    'completed': { label: '完了', next: 'pending' }
  }

  const handleStatusChange = async () => {
    const nextStatus = statusMap[currentStatus]?.next || 'pending'
    setIsLoading(true)

    try {
      await apiClient.put(`/api/v1/tasks/${taskId}`, {
        status: nextStatus
      })
      
      toast({
        title: 'ステータスを更新しました',
        description: `ステータスを「${statusMap[nextStatus].label}」に変更しました`,
        duration: 3000
      })

      if (onStatusChange) {
        onStatusChange(nextStatus)
      }
    } catch (error: any) {
      toast({
        title: 'ステータス更新に失敗しました',
        description: error.response?.data?.detail || 'エラーが発生しました',
        variant: 'destructive',
        duration: 5000
      })
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusColor = () => {
    switch (currentStatus) {
      case 'pending':
        return 'bg-gray-100 text-gray-800'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'completed':
        return 'bg-green-100 text-green-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  return (
    <Button
      onClick={handleStatusChange}
      disabled={isLoading}
      variant="outline"
      size="sm"
      className={`transition-all duration-300 ${getStatusColor()}`}
    >
      {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
      {statusMap[currentStatus]?.label || 'Unknown'}
    </Button>
  )
}

export const TaskEditButton: React.FC<{
  isEditing: boolean
  onToggleEdit: () => void
}> = ({ isEditing, onToggleEdit }) => {
  return (
    <Button
      onClick={onToggleEdit}
      variant="outline"
      size="sm"
      className="transition-all duration-300"
    >
      {isEditing ? (
        <>
          <X className="mr-2 h-4 w-4" />
          キャンセル
        </>
      ) : (
        <>
          <Edit className="mr-2 h-4 w-4" />
          編集
        </>
      )}
    </Button>
  )
}