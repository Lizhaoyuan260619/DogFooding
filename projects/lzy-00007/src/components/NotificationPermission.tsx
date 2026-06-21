import { useState, useEffect } from 'react'
import { Bell, BellOff, BellRing } from 'lucide-react'
import { requestNotificationPermission, getNotificationPermission } from '@/utils/notification'

export default function NotificationPermission() {
  const [permission, setPermission] = useState<NotificationPermission>('default')

  useEffect(() => {
    setPermission(getNotificationPermission())
  }, [])

  const handleRequest = async () => {
    const result = await requestNotificationPermission()
    setPermission(result)
  }

  const statusConfig = {
    granted: {
      label: '已授权',
      color: 'bg-emerald-100 text-emerald-700',
      icon: Bell,
    },
    denied: {
      label: '已拒绝',
      color: 'bg-red-100 text-red-700',
      icon: BellOff,
    },
    default: {
      label: '未请求',
      color: 'bg-amber-100 text-amber-700',
      icon: BellRing,
    },
  }

  const config = statusConfig[permission]
  const StatusIcon = config.icon

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium text-zinc-700">通知权限状态</span>
        <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${config.color}`}>
          <StatusIcon className="w-3.5 h-3.5" />
          {config.label}
        </span>
      </div>

      {permission !== 'granted' && (
        <div className="space-y-2">
          <button
            onClick={handleRequest}
            disabled={permission === 'denied'}
            className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <BellRing className="w-4 h-4" />
            请求通知权限
          </button>

          {permission === 'denied' && (
            <p className="text-xs text-zinc-500 leading-relaxed">
              通知权限已被浏览器拒绝。请在浏览器设置中手动开启：点击地址栏左侧的锁图标 → 网站设置 → 通知 → 允许。
            </p>
          )}
        </div>
      )}
    </div>
  )
}
