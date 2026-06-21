import React, { useState } from 'react'
import {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
  Check,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getToday, getStreak, getTotalCheckIns, isCheckedIn } from '@/utils/date'
import WeekOverview from '@/components/WeekOverview'
import type { Habit } from '@/types'

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
  const checked = isCheckedIn(habit.id, today, checkIns)
  const streak = getStreak(habit.id, checkIns)
  const total = getTotalCheckIns(habit.id, checkIns)

  const IconComponent = iconMap[habit.icon] || Star
  const [animating, setAnimating] = useState(false)

  const handleToggle = () => {
    if (checked) {
      uncheckIn(habit.id, today)
    } else {
      checkIn(habit.id, today)
      setAnimating(true)
      setTimeout(() => setAnimating(false), 400)
    }
  }

  return (
    <div
      className="bg-white rounded-xl shadow-sm hover:shadow-md transition-all duration-200 p-4 flex flex-col gap-3"
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
          <p className="text-sm font-semibold text-gray-800 truncate">{habit.name}</p>
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

      <WeekOverview habitId={habit.id} color={habit.color} />
    </div>
  )
}
