import React from 'react'
import { useAppStore } from '@/store/useAppStore'
import { getLast7DaysStatus, getToday, formatDate, getCheckInsByDate } from '@/utils/date'
import { WEEKDAY_LABELS } from '@/utils/constants'

interface WeekOverviewProps {
  habitId: string
  color: string
}

export default function WeekOverview({ habitId, color }: WeekOverviewProps) {
  const { checkIns } = useAppStore()
  const last7 = getLast7DaysStatus(habitId, checkIns)
  const today = getToday()

  const isMakeup = (dateStr: string) => {
    const dayCheckIns = getCheckInsByDate(dateStr, checkIns)
    const checkIn = dayCheckIns.find(c => c.habitId === habitId)
    return checkIn?.type === 'makeup'
  }

  return (
    <div className="flex items-start justify-between gap-2">
      {last7.map((done, i) => {
        const date = new Date()
        date.setDate(date.getDate() - (6 - i))
        const dateStr = formatDate(date)
        const dayIndex = date.getDay()
        const weekday = WEEKDAY_LABELS[dayIndex]
        const isToday = dateStr === today
        const isMakeupCheckIn = done && isMakeup(dateStr)

        return (
          <div key={i} className="flex flex-col items-center gap-1">
            <div className="relative">
              <div
                className="w-6 h-6 rounded-full transition-all duration-300"
                style={{
                  backgroundColor: done ? color : 'transparent',
                  border: done ? 'none' : `2px solid ${color}40`,
                  boxShadow: done ? `0 2px 8px ${color}40` : 'none',
                }}
              >
                {done && (
                  <svg className="w-full h-full p-1 text-white" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8.5L6.5 12L13 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                )}
              </div>
              {isMakeupCheckIn && (
                <div
                  className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-amber-400 border border-white"
                  title="补卡"
                />
              )}
            </div>
            <span className={`text-[10px] ${isToday ? 'text-emerald-600 font-semibold' : 'text-gray-400'}`}>{weekday}</span>
          </div>
        )
      })}
    </div>
  )
}
