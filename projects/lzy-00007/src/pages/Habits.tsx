import { useState } from 'react'
import { Plus, Pencil, Trash2, History } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getStreak, getTotalCheckIns, isCheckedIn, getToday, formatDate } from '@/utils/date'
import HabitForm from '@/components/HabitForm'
import {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil as PencilIcon, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
} from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil: PencilIcon, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
}

const FREQ_LABELS: Record<string, string> = {
  daily: '每天',
  weekly: '每周',
  monthly: '每月',
}

export default function Habits() {
  const habits = useAppStore((s) => s.habits)
  const checkIns = useAppStore((s) => s.checkIns)
  const deleteHabit = useAppStore((s) => s.deleteHabit)
  const categories = useAppStore((s) => s.categories)

  const [showForm, setShowForm] = useState(false)
  const [editHabitId, setEditHabitId] = useState<string | null>(null)
  const [expandedHabit, setExpandedHabit] = useState<string | null>(null)
  const [filterCategory, setFilterCategory] = useState<string>('all')

  const handleEdit = (id: string) => {
    setEditHabitId(id)
    setShowForm(true)
  }

  const handleAdd = () => {
    setEditHabitId(null)
    setShowForm(true)
  }

  const handleClose = () => {
    setShowForm(false)
    setEditHabitId(null)
  }

  const handleDelete = (id: string) => {
    if (window.confirm('确定要删除这个习惯吗？删除后无法恢复。')) {
      deleteHabit(id)
    }
  }

  const getCategoryName = (categoryId: string) => {
    const cat = categories.find((c) => c.id === categoryId)
    return cat?.name ?? categoryId
  }

  const getCategoryColor = (categoryId: string) => {
    const cat = categories.find((c) => c.id === categoryId)
    return cat?.color ?? '#6B7280'
  }

  const filteredHabits = filterCategory === 'all'
    ? habits
    : habits.filter(h => h.category === filterCategory)

  const getRecentCheckIns = (habitId: string, limit: number = 14) => {
    return checkIns
      .filter(c => c.habitId === habitId)
      .sort((a, b) => b.date.localeCompare(a.date))
      .slice(0, limit)
  }

  return (
    <div className="min-h-screen bg-[#FFFDF7] pb-24">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="font-[Outfit] text-2xl font-bold text-zinc-800">习惯管理</h1>
          <button
            onClick={handleAdd}
            className="flex items-center gap-1.5 px-4 py-2 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-colors shadow-sm shadow-emerald-500/20"
          >
            <Plus className="w-4 h-4" />
            添加习惯
          </button>
        </div>

        <div className="flex gap-2 overflow-x-auto pb-1">
          <button
            onClick={() => setFilterCategory('all')}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
              filterCategory === 'all'
                ? 'bg-emerald-500 text-white'
                : 'bg-white text-gray-500 hover:bg-gray-50 shadow-sm'
            }`}
          >
            全部
          </button>
          {categories.map(cat => (
            <button
              key={cat.id}
              onClick={() => setFilterCategory(cat.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-colors ${
                filterCategory === cat.id
                  ? 'text-white'
                  : 'bg-white text-gray-500 hover:bg-gray-50 shadow-sm'
              }`}
              style={filterCategory === cat.id ? { backgroundColor: cat.color } : undefined}
            >
              {cat.name}
            </button>
          ))}
        </div>

        {filteredHabits.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <Star className="w-8 h-8 text-gray-300" />
            </div>
            <p className="text-gray-400 text-sm">暂无习惯，点击上方按钮添加</p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredHabits.map((habit) => {
              const streak = getStreak(habit.id, checkIns)
              const total = getTotalCheckIns(habit.id, checkIns)
              const isExpanded = expandedHabit === habit.id
              const recentCheckIns = getRecentCheckIns(habit.id)
              const IconComponent = iconMap[habit.icon] || Star
              const today = getToday()
              const checkedToday = isCheckedIn(habit.id, today, checkIns)

              return (
                <div
                  key={habit.id}
                  className="bg-white rounded-xl shadow-sm overflow-hidden transition-all duration-200 hover:shadow-md"
                >
                  <div className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-3">
                        <div
                          className="w-10 h-10 rounded-full flex items-center justify-center shrink-0"
                          style={{ backgroundColor: habit.color + '20', color: habit.color }}
                        >
                          <IconComponent size={20} />
                        </div>
                        <div>
                          <span className="text-sm font-semibold text-zinc-800">{habit.name}</span>
                          <div className="flex items-center gap-2 mt-1">
                            <span
                              className="px-2 py-0.5 rounded-full text-[10px] font-medium text-white"
                              style={{ backgroundColor: getCategoryColor(habit.category) }}
                            >
                              {getCategoryName(habit.category)}
                            </span>
                            <span className="px-2 py-0.5 rounded-full text-[10px] font-medium bg-zinc-100 text-zinc-600">
                              {FREQ_LABELS[habit.frequencyType]}
                              {habit.frequencyCount > 1 ? ` ${habit.frequencyCount}次` : ''}
                            </span>
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {checkedToday && (
                          <span className="text-xs text-emerald-500 font-medium mr-2">今日已打卡</span>
                        )}
                        <button
                          onClick={() => setExpandedHabit(isExpanded ? null : habit.id)}
                          className="p-1.5 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
                        >
                          <History className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleEdit(habit.id)}
                          className="p-1.5 text-zinc-400 hover:text-zinc-600 hover:bg-zinc-100 rounded-lg transition-colors"
                        >
                          <Pencil className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleDelete(habit.id)}
                          className="p-1.5 text-zinc-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <div className="flex items-center gap-4 text-xs text-zinc-500 mt-3">
                      <span className="flex items-center gap-1">
                        <Flame size={12} style={{ color: streak > 0 ? '#F97316' : undefined }} />
                        <span style={{ color: streak > 0 ? '#F97316' : undefined }}>连续 {streak} 天</span>
                      </span>
                      <span>累计 {total} 次</span>
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="border-t border-gray-100 px-4 py-3 bg-gray-50/50 animate-fade-in">
                      <p className="text-xs font-medium text-gray-500 mb-2">最近打卡记录</p>
                      {recentCheckIns.length === 0 ? (
                        <p className="text-xs text-gray-400">暂无打卡记录</p>
                      ) : (
                        <div className="flex flex-wrap gap-1.5">
                          {recentCheckIns.map(ci => (
                            <span
                              key={ci.id}
                              className="text-[10px] px-2 py-1 rounded-md bg-white text-gray-600 border border-gray-100"
                            >
                              {ci.date}
                            </span>
                          ))}
                        </div>
                      )}

                      <div className="mt-3">
                        <p className="text-xs font-medium text-gray-500 mb-2">近30天打卡</p>
                        <div className="flex gap-[2px]">
                          {Array.from({ length: 30 }, (_, i) => {
                            const d = new Date()
                            d.setDate(d.getDate() - (29 - i))
                            const dateStr = formatDate(d)
                            const done = isCheckedIn(habit.id, dateStr, checkIns)
                            return (
                              <div
                                key={i}
                                className="w-2.5 h-2.5 rounded-[1px]"
                                style={{
                                  backgroundColor: done ? habit.color : '#f3f4f6',
                                }}
                                title={dateStr}
                              />
                            )
                          })}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        )}
      </div>

      {showForm && (
        <HabitForm habitId={editHabitId} onClose={handleClose} />
      )}
    </div>
  )
}
