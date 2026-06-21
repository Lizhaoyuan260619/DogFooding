import { useNavigate } from 'react-router-dom'
import { Plus, Sparkles, Target, Flame, CheckCircle2, TrendingUp } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getToday, formatDate, getStreak, isCheckedIn } from '@/utils/date'
import HabitCard from '@/components/HabitCard'

export default function Dashboard() {
  const navigate = useNavigate()
  const habits = useAppStore((s) => s.habits)
  const checkIns = useAppStore((s) => s.checkIns)
  const initDemoData = useAppStore((s) => s.initDemoData)

  const today = getToday()
  const formattedDate = formatDate(new Date(), 'M月d日 EEEE')

  const todayCompleted = habits.filter((h) => isCheckedIn(h.id, today, checkIns)).length
  const todayRate = habits.length > 0 ? Math.round((todayCompleted / habits.length) * 100) : 0

  const longestStreak = habits.reduce((max, h) => {
    const streak = getStreak(h.id, checkIns)
    return streak > max ? streak : max
  }, 0)

  if (habits.length === 0) {
    return (
      <div className="min-h-screen bg-[#FFFDF7] flex items-center justify-center p-6">
        <div className="bg-white rounded-2xl p-8 max-w-sm w-full text-center shadow-sm">
          <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-emerald-600" />
          </div>
          <h2 className="font-[Outfit] text-xl font-semibold text-zinc-800 mb-2">
            欢迎使用习惯追踪
          </h2>
          <p className="text-sm text-zinc-500 mb-6">
            开始记录你的第一个习惯，让改变从今天发生
          </p>
          <button
            onClick={() => {
              initDemoData()
            }}
            className="w-full px-4 py-2.5 bg-emerald-500 text-white rounded-xl text-sm font-medium hover:bg-emerald-600 transition-colors shadow-sm shadow-emerald-500/20"
          >
            开始你的第一个习惯
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-[#FFFDF7] pb-24">
      <div className="p-6 space-y-6">
        <div>
          <h1 className="font-[Outfit] text-2xl font-bold text-zinc-800">今日打卡</h1>
          <p className="text-sm text-zinc-500 mt-1">{formattedDate}</p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <Target className="w-5 h-5 text-blue-500 mx-auto mb-1" />
            <p className="font-[Outfit] text-2xl font-bold text-zinc-800">{habits.length}</p>
            <p className="text-xs text-zinc-500">习惯总数</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 mx-auto mb-1" />
            <p className="font-[Outfit] text-2xl font-bold text-zinc-800">{todayCompleted}</p>
            <p className="text-xs text-zinc-500">今日完成</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <Flame className="w-5 h-5 text-orange-500 mx-auto mb-1" />
            <p className="font-[Outfit] text-2xl font-bold text-zinc-800">{longestStreak}</p>
            <p className="text-xs text-zinc-500">最长连续</p>
          </div>
          <div className="bg-white rounded-xl p-4 text-center shadow-sm">
            <TrendingUp className="w-5 h-5 text-purple-500 mx-auto mb-1" />
            <p className="font-[Outfit] text-2xl font-bold text-zinc-800">{todayRate}%</p>
            <p className="text-xs text-zinc-500">今日完成率</p>
          </div>
        </div>

        {todayRate < 100 && todayRate > 0 && (
          <div className="bg-white rounded-xl p-4 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-zinc-700">今日进度</span>
              <span className="text-sm text-emerald-600 font-medium">{todayCompleted}/{habits.length}</span>
            </div>
            <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full transition-all duration-500"
                style={{ width: `${todayRate}%` }}
              />
            </div>
          </div>
        )}

        {todayRate === 100 && (
          <div className="bg-gradient-to-r from-emerald-50 to-teal-50 rounded-xl p-4 shadow-sm border border-emerald-100">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircle2 className="w-5 h-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-sm font-semibold text-emerald-800">🎉 太棒了！今日习惯全部完成！</p>
                <p className="text-xs text-emerald-600">继续保持，养成好习惯！</p>
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {habits.map((habit) => (
            <HabitCard key={habit.id} habit={habit} />
          ))}
        </div>
      </div>

      <button
        onClick={() => navigate('/habits')}
        className="fixed bottom-24 md:bottom-6 right-6 w-14 h-14 bg-emerald-500 text-white rounded-full shadow-lg shadow-emerald-500/30 flex items-center justify-center hover:bg-emerald-600 transition-colors z-10 hover:scale-105 active:scale-95"
      >
        <Plus className="w-6 h-6" />
      </button>
    </div>
  )
}
