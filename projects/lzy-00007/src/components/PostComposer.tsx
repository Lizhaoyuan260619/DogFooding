import React, { useState } from 'react'
import { Send, Image, X, Target } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import type { Habit } from '@/types'

interface PostComposerProps {
  onSuccess?: () => void
}

export default function PostComposer({ onSuccess }: PostComposerProps) {
  const { habits, userProfile, createPost } = useAppStore()
  const [content, setContent] = useState('')
  const [selectedHabit, setSelectedHabit] = useState<Habit | null>(null)
  const [showHabitSelector, setShowHabitSelector] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = () => {
    if (!content.trim()) return

    setIsSubmitting(true)
    setTimeout(() => {
      createPost({
        content: content.trim(),
        habitId: selectedHabit?.id,
        isCheckInPost: !!selectedHabit,
        checkInDate: new Date().toISOString().split('T')[0],
      })
      setContent('')
      setSelectedHabit(null)
      setIsSubmitting(false)
      onSuccess?.()
    }, 300)
  }

  const handleSelectHabit = (habit: Habit) => {
    setSelectedHabit(habit)
    setShowHabitSelector(false)
    if (!content) {
      setContent(`今天完成了「${habit.name}」打卡！💪`)
    }
  }

  return (
    <div className="bg-white rounded-2xl shadow-sm p-4 mb-6">
      <div className="flex gap-3">
        <img
          src={userProfile.avatar}
          alt={userProfile.name}
          className="w-12 h-12 rounded-full object-cover flex-shrink-0"
        />
        <div className="flex-1">
          <textarea
            value={content}
            onChange={(e) => setContent(e.target.value)}
            placeholder="分享今天的打卡心得..."
            className="w-full p-3 border border-gray-200 rounded-xl resize-none focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
            rows={3}
            maxLength={500}
          />

          <div className="flex items-center justify-between mt-3">
            <div className="flex gap-2">
              <button
                onClick={() => setShowHabitSelector(!showHabitSelector)}
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  selectedHabit
                    ? 'text-white'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
                style={selectedHabit ? { backgroundColor: selectedHabit.color } : {}}
              >
                <Target size={16} />
                {selectedHabit ? selectedHabit.name : '关联习惯'}
              </button>

              {selectedHabit && (
                <button
                  onClick={() => setSelectedHabit(null)}
                  className="p-2 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
                >
                  <X size={16} />
                </button>
              )}

              <button className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 transition-all">
                <Image size={16} />
                图片
              </button>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs text-gray-400">
                {content.length}/500
              </span>
              <button
                onClick={handleSubmit}
                disabled={!content.trim() || isSubmitting}
                className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-xl font-medium text-sm transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Send size={16} />
                {isSubmitting ? '发布中...' : '发布'}
              </button>
            </div>
          </div>

          {showHabitSelector && habits.length > 0 && (
            <div className="mt-3 p-3 bg-gray-50 rounded-xl">
              <p className="text-xs text-gray-500 mb-2">选择要关联的习惯</p>
              <div className="flex flex-wrap gap-2">
                {habits.map((habit) => (
                  <button
                    key={habit.id}
                    onClick={() => handleSelectHabit(habit)}
                    className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105"
                    style={{
                      backgroundColor: habit.color + '20',
                      color: habit.color,
                    }}
                  >
                    <span className="w-2 h-2 rounded-full" style={{ backgroundColor: habit.color }} />
                    {habit.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
