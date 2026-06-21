import { useEffect } from 'react'
import { Bell, Download, Info, Trash2 } from 'lucide-react'
import NotificationPermission from '@/components/NotificationPermission'
import ReminderSettings from '@/components/ReminderSettings'
import ExportPanel from '@/components/ExportPanel'
import { useAppStore } from '@/store/useAppStore'
import { scheduleAllNotifications } from '@/utils/notification'

export default function Settings() {
  const habits = useAppStore((s) => s.habits)

  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'granted') {
      scheduleAllNotifications(habits)
    }
  }, [habits])

  const handleClearData = () => {
    if (window.confirm('确定要清除所有数据吗？此操作不可恢复！')) {
      localStorage.removeItem('habit-tracker-storage')
      window.location.reload()
    }
  }

  return (
    <div className="min-h-screen bg-[#FFFDF7] pb-24">
      <div className="p-6 space-y-6 max-w-2xl">
        <h1 className="font-[Outfit] text-2xl font-bold text-zinc-800">设置</h1>

        <div className="bg-white rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Bell className="w-5 h-5 text-emerald-500" />
            <h2 className="font-[Outfit] text-base font-semibold text-zinc-800">通知设置</h2>
          </div>
          <NotificationPermission />
          <div className="border-t border-zinc-100 pt-4">
            <ReminderSettings />
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Download className="w-5 h-5 text-emerald-500" />
            <h2 className="font-[Outfit] text-base font-semibold text-zinc-800">数据导出</h2>
          </div>
          <ExportPanel />
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Info className="w-5 h-5 text-emerald-500" />
            <h2 className="font-[Outfit] text-base font-semibold text-zinc-800">关于</h2>
          </div>
          <div className="space-y-2 text-sm text-zinc-500">
            <p>习惯追踪器 v1.0.0</p>
            <p>记录每一天的坚持，让好习惯成为生活的一部分。</p>
          </div>
        </div>

        <div className="bg-white rounded-xl p-5 shadow-sm space-y-4">
          <div className="flex items-center gap-2">
            <Trash2 className="w-5 h-5 text-red-400" />
            <h2 className="font-[Outfit] text-base font-semibold text-red-600">危险操作</h2>
          </div>
          <p className="text-sm text-zinc-500">清除所有数据将删除你的所有习惯和打卡记录，此操作不可恢复。</p>
          <button
            onClick={handleClearData}
            className="flex items-center gap-2 px-4 py-2 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition-colors border border-red-200"
          >
            <Trash2 className="w-4 h-4" />
            清除所有数据
          </button>
        </div>
      </div>
    </div>
  )
}
