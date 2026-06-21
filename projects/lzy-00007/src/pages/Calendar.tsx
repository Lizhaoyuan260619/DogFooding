import { useState } from 'react'
import { CheckCircle2, Circle, RefreshCw } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getCheckInsByDate, getToday, getMonthlyMakeupCount, isWithinMakeupRange } from '@/utils/date'
import HeatmapCalendar from '@/components/HeatmapCalendar'
import CheckInModal from '@/components/CheckInModal'
import { MAX_MAKEUP_PER_MONTH } from '@/utils/constants'
import {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import type { Habit } from '@/types'

const iconMap: Record<string, LucideIcon> = {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
}

export default function Calendar() {
  const { checkIns, habits, checkIn, uncheckIn } = useAppStore()
  const today = getToday()
  const [selectedDate, setSelectedDate] = useState<string>(today)
  const [selectedHabit, setSelectedHabit] = useState<Habit | null>(null)

  const dayCheckIns = getCheckInsByDate(selectedDate, checkIns)
  const completedHabitIds = new Set(dayCheckIns.map(c => c.habitId))
  const makeupCount = getMonthlyMakeupCount(checkIns)
  const isToday = selectedDate === today
  const canMakeupDate = !isToday && isWithinMakeupRange(selectedDate)

  const handleToggle = (habit: Habit) => {
    if (completedHabitIds.has(habit.id)) {
      uncheckIn(habit.id, selectedDate)
    } else if (isToday) {
      checkIn(habit.id, selectedDate)
    } else if (canMakeupDate) {
      setSelectedHabit(habit)
    }
  }

  const handleHabitClick = (habit: Habit) => {
    setSelectedHabit(habit)
  }

  const formattedDate = (() => {
    const d = new Date(selectedDate + 'T00:00:00')
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return `${d.getMonth() + 1}月${d.getDate()}日 ${weekdays[d.getDay()]}`
  })()

  const getCheckInForHabit = (habitId: string) => {
    return dayCheckIns.find(c => c.habitId === habitId)
  }

  return (
    <div className="min-h-screen bg-[#FFFDF7] pb-24">
      <div className="p-6 space-y-6">
        <h1 className="font-[Outfit] text-2xl font-bold text-zinc-800">日历热力图</h1>
        <HeatmapCalendar />

        <div className="bg-white rounded-xl shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-base font-semibold text-gray-800">{formattedDate}</h3>
              {!isToday && canMakeupDate && (
                <p className="text-xs text-amber-600 mt-0.5 flex items-center gap-1">
                  <RefreshCw size={12} />
                  可补卡 · 本月已补 {makeupCount}/{MAX_MAKEUP_PER_MONTH} 次
                </p>
              )}
            </div>
            <input
              type="date"
              value={selectedDate}
              onChange={e => setSelectedDate(e.target.value)}
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            />
          </div>

          {habits.length === 0 ? (
            <div className="py-8 text-center text-gray-400 text-sm">
              暂无习惯，请先添加
            </div>
          ) : (
            <div className="space-y-2">
              {habits.map(habit => {
                const isCompleted = completedHabitIds.has(habit.id)
                const checkInRecord = getCheckInForHabit(habit.id)
                const isMakeup = checkInRecord?.type === 'makeup'
                const IconComponent = iconMap[habit.icon] || Star
                const isFuture = selectedDate > today

                return (
                  <div
                    key={habit.id}
                    onClick={() => !isFuture && handleHabitClick(habit)}
                    className={`flex items-center gap-3 p-3 rounded-xl transition-all duration-200 cursor-pointer ${
                      isCompleted ? 'bg-emerald-50' : 'hover:bg-gray-50'
                    } ${isFuture ? 'opacity-40 cursor-not-allowed' : ''}`}
                  >
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        if (!isFuture) handleToggle(habit)
                      }}
                      disabled={isFuture || (!isToday && !canMakeupDate && !isCompleted)}
                      className="shrink-0"
                    >
                      {isCompleted ? (
                        <CheckCircle2
                          size={22}
                          style={{ color: habit.color }}
                          className="transition-all duration-200"
                        />
                      ) : (
                        <Circle
                          size={22}
                          className={`transition-colors ${
                            isFuture || (!isToday && !canMakeupDate)
                              ? 'text-gray-200'
                              : 'text-gray-300 hover:text-gray-400'
                          }`}
                        />
                      )}
                    </button>
                    <div
                      className="w-8 h-8 rounded-full flex items-center justify-center shrink-0"
                      style={{ backgroundColor: habit.color + '20', color: habit.color }}
                    >
                      <IconComponent size={16} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className={`text-sm font-medium truncate ${isCompleted ? 'text-gray-800' : 'text-gray-500'}`}>
                          {habit.name}
                        </span>
                        {isMakeup && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 flex items-center gap-0.5 shrink-0">
                            <RefreshCw size={10} />
                            补卡
                          </span>
                        )}
                      </div>
                      {checkInRecord && (checkInRecord.checkInTime || checkInRecord.location) && (
                        <div className="flex items-center gap-2 text-xs text-gray-400 mt-0.5">
                          {checkInRecord.checkInTime && (
                            <span className="flex items-center gap-0.5">
                              <Clock size={10} />
                              {checkInRecord.checkInTime}
                            </span>
                          )}
                          {checkInRecord.location && (
                            <span className="flex items-center gap-0.5 truncate">
                              <span className="shrink-0">📍</span>
                              <span className="truncate">{checkInRecord.location}</span>
                            </span>
                          )}
                        </div>
                      )}
                    </div>
                    {isCompleted && (
                      <span
                        className="text-xs font-medium px-2 py-0.5 rounded-full shrink-0"
                        style={{ backgroundColor: habit.color + '20', color: habit.color }}
                      >
                        {isMakeup ? '已补卡' : '已完成'}
                      </span>
                    )}
                    {!isCompleted && canMakeupDate && (
                      <span className="text-xs text-amber-600 shrink-0">
                        可补卡
                      </span>
                    )}
                  </div>
                )
              })}

              <div className="pt-3 border-t border-gray-100 mt-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">完成进度</span>
                  <span className="font-medium text-gray-800">
                    {completedHabitIds.size}/{habits.length}
                  </span>
                </div>
                <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden mt-2">
                  <div
                    className="h-full bg-emerald-500 rounded-full transition-all duration-500"
                    style={{ width: `${habits.length > 0 ? (completedHabitIds.size / habits.length) * 100 : 0}%` }}
                  />
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {selectedHabit && (
        <CheckInModal
          habit={selectedHabit}
          date={selectedDate}
          onClose={() => setSelectedHabit(null)}
        />
      )}
    </div>
  )
}
