import React, { useMemo } from 'react'
import {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getCompletionRate, formatDate } from '@/utils/date'
import { parseISO } from 'date-fns'

const iconMap: Record<string, LucideIcon> = {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
}

interface RankedHabit {
  id: string
  name: string
  icon: string
  color: string
  rate: number
}

export default function HabitRanking() {
  const { habits, checkIns } = useAppStore()

  const { top5, bottom5 } = useMemo(() => {
    if (habits.length === 0) return { top5: [], bottom5: [] }

    const ranked: RankedHabit[] = habits.map(h => {
      const start = formatDate(parseISO(h.createdAt))
      const end = formatDate(new Date())
      const rate = getCompletionRate(h, checkIns, start, end)
      return {
        id: h.id,
        name: h.name,
        icon: h.icon,
        color: h.color,
        rate: Math.round(rate * 10) / 10,
      }
    })

    ranked.sort((a, b) => b.rate - a.rate)

    const top5 = ranked.slice(0, 5)
    const bottom5 = [...ranked].reverse().slice(0, 5)

    return { top5, bottom5 }
  }, [habits, checkIns])

  const renderItem = (item: RankedHabit, rank: number, isTop: boolean) => {
    const IconComponent = iconMap[item.icon] || Star
    return (
      <div key={item.id} className="flex items-center gap-3 py-2">
        <span
          className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold shrink-0 ${
            isTop
              ? rank <= 3
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-gray-100 text-gray-500'
              : rank <= 3
                ? 'bg-red-100 text-red-700'
                : 'bg-gray-100 text-gray-500'
          }`}
        >
          {rank}
        </span>
        <div
          className="w-7 h-7 rounded-full flex items-center justify-center shrink-0"
          style={{ backgroundColor: item.color + '20', color: item.color }}
        >
          <IconComponent size={14} />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-sm text-gray-700 truncate">{item.name}</span>
            <span
              className={`text-xs font-semibold ml-2 ${isTop ? 'text-emerald-600' : 'text-red-500'}`}
            >
              {item.rate}%
            </span>
          </div>
          <div className="w-full h-1.5 bg-gray-100 rounded-full overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, item.rate)}%`,
                backgroundColor: isTop ? '#10B981' : '#EF4444',
              }}
            />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">习惯排行</h3>

      {habits.length === 0 ? (
        <div className="py-8 text-center text-gray-400 text-sm">暂无习惯数据</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <div className="flex items-center gap-1.5 mb-3">
              <Trophy size={14} className="text-emerald-500" />
              <span className="text-sm font-medium text-emerald-600">完成率最高</span>
            </div>
            <div className="divide-y divide-gray-50">
              {top5.map((item, i) => renderItem(item, i + 1, true))}
            </div>
          </div>

          <div>
            <div className="flex items-center gap-1.5 mb-3">
              <Target size={14} className="text-red-400" />
              <span className="text-sm font-medium text-red-500">需要加油</span>
            </div>
            <div className="divide-y divide-gray-50">
              {bottom5.map((item, i) => renderItem(item, i + 1, false))}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
