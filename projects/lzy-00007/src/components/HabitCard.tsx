import React, { useState } from 'react'
import {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
  Check, ChevronRight, MapPin, FileText, RefreshCw,
} from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getToday, getStreak, getTotalCheckIns } from '@/utils/date'
import WeekOverview from '@/components/WeekOverview'
import CheckInModal from '@/components/CheckInModal'
import type { Habit } from '@/types'
import type { LucideIcon } from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
}

interface HabitCardProps {
  habit: Habit
}

export default function HabitCard({ habit }: HabitCardProps) {
  const { checkIns, checkIn, uncheckIn } = useAppStore()
  const today = getToday()
  const todayCheckIn = checkIns.find(c => c.habitId === habit.id && c.date === today)
  const checked = !!todayCheckIn
  const streak = getStreak(habit.id, checkIns)
  const total = getTotalCheckIns(habit.id, checkIns)

  const IconComponent = iconMap[habit.icon] || Star
  const [animating, setAnimating] = useState(false)
  const [showModal, setShowModal] = useState(false)

  const handleToggle = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (checked) {
      uncheckIn(habit.id, today)
    } else {
      checkIn(habit.id, today)
      setAnimating(true)
      setTimeout(() => setAnimating(false), 400)
    }
  }

  const handleCardClick = () => {
    setShowModal(true)
  }

  return (
    <>
      <div
        onClick={handleCardClick}
        className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-4 flex flex-col gap-3 cursor-pointer"
        style={{
          borderLeft: checked ? `3px solid ${habit.color}` : '3px solid transparent',
        }}
      >
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-full flex items-center justify-center shrink-0 transition-all duration-300"
            style={{
              backgroundColor: checked ? habit.color : habit.color + '20',
              color: checked ? 'white' : habit.color,
            }}
          >
            <IconComponent size={20} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <p className="text-sm font-semibold text-gray-800 truncate">{habit.name}</p>
              {todayCheckIn?.type === 'makeup' && (
                <span className="text-[10px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 flex items-center gap-0.5 shrink-0">
                  <RefreshCw size={10} />
                  补卡
                </span>
              )}
            </div>
            <div className="flex items-center gap-3 text-xs text-gray-400 mt-0.5">
              <span className="flex items-center gap-1">
                <Flame size={12} style={{ color: streak > 0 ? '#F97316' : undefined }} />
                <span style={{ color: streak > 0 ? '#F97316' : undefined }}>{streak}天</span>
              </span>
              <span>共{total}次</span>
            </div>
          </div>
          <button
            onClick={handleToggle}
            className={`relative w-12 h-12 rounded-full flex items-center justify-center transition-all duration-300 shrink-0 ${
              animating ? 'animate-check-in' : ''
            }`}
            style={{
              backgroundColor: checked ? habit.color : 'transparent',
              border: checked ? 'none' : `2px solid ${habit.color}`,
              color: checked ? 'white' : habit.color,
              boxShadow: checked ? `0 4px 12px ${habit.color}40` : 'none',
            }}
          >
            {checked && <Check size={20} strokeWidth={3} />}
          </button>
        </div>

        {todayCheckIn && (todayCheckIn.remark || todayCheckIn.checkInTime || todayCheckIn.location) && (
          <div className="bg-gray-50 rounded-lg p-2.5 space-y-1">
            {todayCheckIn.checkInTime && (
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <Clock size={12} />
                <span>{todayCheckIn.checkInTime}</span>
              </div>
            )}
            {todayCheckIn.location && (
              <div className="flex items-center gap-1.5 text-xs text-gray-500">
                <MapPin size={12} />
                <span className="truncate">{todayCheckIn.location}</span>
              </div>
            )}
            {todayCheckIn.remark && (
              <div className="flex items-start gap-1.5 text-xs text-gray-600">
                <FileText size={12} className="mt-0.5 shrink-0" />
                <span className="line-clamp-2">{todayCheckIn.remark}</span>
              </div>
            )}
          </div>
        )}

        <WeekOverview habitId={habit.id} color={habit.color} />

        <div className="flex items-center justify-end text-xs text-gray-400">
          <span>查看详情</span>
          <ChevronRight size={12} />
        </div>
      </div>

      {showModal && (
        <CheckInModal
          habit={habit}
          date={today}
          onClose={() => setShowModal(false)}
        />
      )}
    </>
  )
}
