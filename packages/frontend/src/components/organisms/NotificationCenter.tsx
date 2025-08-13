import React, { useEffect, useState } from 'react'
import { Bell, X, CheckCircle, AlertCircle, Info, XCircle } from 'lucide-react'
import { Button } from '../atoms/button'
import { Card } from '../atoms/card'
import { formatDistanceToNow } from 'date-fns'
import { ja } from 'date-fns/locale'

interface Notification {
  id: string
  type: 'success' | 'error' | 'warning' | 'info'
  title: string
  message: string
  timestamp: Date
  read: boolean
  action?: {
    label: string
    onClick: () => void
  }
}

export const NotificationCenter: React.FC = () => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [isOpen, setIsOpen] = useState(false)
  const [unreadCount, setUnreadCount] = useState(0)

  // Subscribe to notification events
  useEffect(() => {
    const handleNotification = (event: CustomEvent<Notification>) => {
      setNotifications(prev => [event.detail, ...prev])
      setUnreadCount(prev => prev + 1)
    }

    window.addEventListener('app:notification' as any, handleNotification)
    
    return () => {
      window.removeEventListener('app:notification' as any, handleNotification)
    }
  }, [])

  const markAsRead = (id: string) => {
    setNotifications(prev => 
      prev.map(n => n.id === id ? { ...n, read: true } : n)
    )
    setUnreadCount(prev => Math.max(0, prev - 1))
  }

  const markAllAsRead = () => {
    setNotifications(prev => prev.map(n => ({ ...n, read: true })))
    setUnreadCount(0)
  }

  const removeNotification = (id: string) => {
    const notification = notifications.find(n => n.id === id)
    if (notification && !notification.read) {
      setUnreadCount(prev => Math.max(0, prev - 1))
    }
    setNotifications(prev => prev.filter(n => n.id !== id))
  }

  const getIcon = (type: Notification['type']) => {
    switch (type) {
      case 'success':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'error':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'warning':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />
      case 'info':
        return <Info className="h-5 w-5 text-blue-600" />
    }
  }

  return (
    <div className="relative">
      <Button
        variant="ghost"
        size="sm"
        onClick={() => setIsOpen(!isOpen)}
        className="relative"
      >
        <Bell className="h-5 w-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full h-5 w-5 flex items-center justify-center">
            {unreadCount > 9 ? '9+' : unreadCount}
          </span>
        )}
      </Button>

      {isOpen && (
        <>
          <div 
            className="fixed inset-0 z-40" 
            onClick={() => setIsOpen(false)}
          />
          <Card className="absolute right-0 mt-2 w-96 max-h-[500px] overflow-hidden z-50 shadow-lg">
            <div className="p-4 border-b flex items-center justify-between">
              <h3 className="font-semibold">通知</h3>
              <div className="flex items-center gap-2">
                {unreadCount > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={markAllAsRead}
                    className="text-sm text-blue-600 hover:text-blue-700"
                  >
                    すべて既読にする
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setIsOpen(false)}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
            </div>

            <div className="overflow-y-auto max-h-[400px]">
              {notifications.length === 0 ? (
                <div className="p-8 text-center text-secondary">
                  通知はありません
                </div>
              ) : (
                <div className="divide-y">
                  {notifications.map((notification) => (
                    <div
                      key={notification.id}
                      className={`p-4 hover:bg-gray-50 transition-colors ${
                        !notification.read ? 'bg-blue-50' : ''
                      }`}
                      onClick={() => !notification.read && markAsRead(notification.id)}
                    >
                      <div className="flex items-start gap-3">
                        <div className="flex-shrink-0 mt-1">
                          {getIcon(notification.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <p className="font-medium text-sm">
                                {notification.title}
                              </p>
                              <p className="text-sm text-gray-600 mt-1">
                                {notification.message}
                              </p>
                              {notification.action && (
                                <Button
                                  variant="link"
                                  size="sm"
                                  className="mt-2 p-0 h-auto text-blue-600"
                                  onClick={(e) => {
                                    e.stopPropagation()
                                    notification.action!.onClick()
                                    setIsOpen(false)
                                  }}
                                >
                                  {notification.action.label}
                                </Button>
                              )}
                            </div>
                            <Button
                              variant="ghost"
                              size="sm"
                              className="ml-2 h-6 w-6 p-0"
                              onClick={(e) => {
                                e.stopPropagation()
                                removeNotification(notification.id)
                              }}
                            >
                              <X className="h-3 w-3" />
                            </Button>
                          </div>
                          <p className="text-xs text-secondary mt-2">
                            {formatDistanceToNow(notification.timestamp, {
                              addSuffix: true,
                              locale: ja
                            })}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </Card>
        </>
      )}
    </div>
  )
}

// Helper function to send notifications
export const sendNotification = (
  notification: Omit<Notification, 'id' | 'timestamp' | 'read'>
) => {
  const event = new CustomEvent('app:notification', {
    detail: {
      ...notification,
      id: Date.now().toString(),
      timestamp: new Date(),
      read: false
    }
  })
  window.dispatchEvent(event)
}