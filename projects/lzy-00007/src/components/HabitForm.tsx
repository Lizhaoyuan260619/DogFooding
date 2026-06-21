import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { cn } from '@/lib/utils'
import { useAppStore } from '@/store/useAppStore'
import { WEEKDAY_LABELS } from '@/utils/constants'
import type { HabitFormData, FormErrors } from '@/types'
import IconPicker from '@/components/IconPicker'
import ColorPicker from '@/components/ColorPicker'
import FrequencySelector from '@/components/FrequencySelector'

interface HabitFormProps {
  habitId?: string
  onClose: () => void
}

const INITIAL_FORM: HabitFormData = {
  name: '',
  icon: 'Dumbbell',
  color: '#10B981',
  category: '',
  frequencyType: 'daily',
  frequencyCount: 1,
  reminderDays: [],
  reminderTime: '09:00',
  reminderEnabled: false,
}

export default function HabitForm({ habitId, onClose }: HabitFormProps) {
  const { habits, categories, addHabit, updateHabit } = useAppStore()
  const [form, setForm] = useState<HabitFormData>(INITIAL_FORM)
  const [errors, setErrors] = useState<FormErrors>({})

  useEffect(() => {
    if (habitId) {
      const habit = habits.find((h) => h.id === habitId)
      if (habit) {
        setForm({
          name: habit.name,
          icon: habit.icon,
          color: habit.color,
          category: habit.category,
          frequencyType: habit.frequencyType,
          frequencyCount: habit.frequencyCount,
          reminderDays: habit.reminderDays,
          reminderTime: habit.reminderTime,
          reminderEnabled: habit.reminderEnabled,
        })
      }
    }
  }, [habitId, habits])

  const validate = (): boolean => {
    const newErrors: FormErrors = {}
    if (!form.name.trim()) {
      newErrors.name = '请输入习惯名称'
    }
    if (!form.category) {
      newErrors.category = '请选择分类'
    }
    if (form.frequencyCount < 1) {
      newErrors.frequencyCount = '次数必须大于0'
    }
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = () => {
    if (!validate()) return

    if (habitId) {
      updateHabit(habitId, form)
    } else {
      addHabit(form)
    }
    onClose()
  }

  const toggleReminderDay = (day: number) => {
    if (form.reminderDays.includes(day)) {
      setForm({ ...form, reminderDays: form.reminderDays.filter((d) => d !== day) })
    } else {
      setForm({ ...form, reminderDays: [...form.reminderDays, day] })
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
      <div className="mx-4 w-full max-w-lg rounded-2xl bg-white shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-stone-100 px-6 py-4">
          <h2 className="text-lg font-semibold text-stone-800">
            {habitId ? '编辑习惯' : '创建新习惯'}
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg p-1.5 text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
          >
            <X size={20} />
          </button>
        </div>

        <div className="space-y-5 px-6 py-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">习惯名称</label>
            <input
              type="text"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              placeholder="例如：每天跑步30分钟"
              className={cn(
                'w-full rounded-xl border bg-white px-4 py-2.5 text-sm text-stone-700 outline-none transition-colors placeholder:text-stone-400',
                errors.name
                  ? 'border-red-300 focus:border-red-400 focus:ring-2 focus:ring-red-100'
                  : 'border-stone-200 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100'
              )}
            />
            {errors.name && <p className="mt-1 text-xs text-red-500">{errors.name}</p>}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">选择图标</label>
            <IconPicker value={form.icon} onChange={(icon) => setForm({ ...form, icon })} />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">选择颜色</label>
            <ColorPicker value={form.color} onChange={(color) => setForm({ ...form, color })} />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">分类</label>
            <select
              value={form.category}
              onChange={(e) => setForm({ ...form, category: e.target.value })}
              className={cn(
                'w-full rounded-xl border bg-white px-4 py-2.5 text-sm outline-none transition-colors',
                !form.category && 'text-stone-400',
                errors.category
                  ? 'border-red-300 focus:border-red-400 focus:ring-2 focus:ring-red-100'
                  : 'border-stone-200 focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100',
                form.category && 'text-stone-700'
              )}
            >
              <option value="">请选择分类</option>
              {categories.map((cat) => (
                <option key={cat.id} value={cat.id}>
                  {cat.name}
                </option>
              ))}
            </select>
            {errors.category && <p className="mt-1 text-xs text-red-500">{errors.category}</p>}
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-stone-700">频率</label>
            <FrequencySelector
              frequencyType={form.frequencyType}
              frequencyCount={form.frequencyCount}
              reminderDays={form.reminderDays}
              onTypeChange={(type) => setForm({ ...form, frequencyType: type })}
              onCountChange={(count) => setForm({ ...form, frequencyCount: count })}
              onReminderDaysChange={(days) => setForm({ ...form, reminderDays: days })}
            />
            {errors.frequencyCount && (
              <p className="mt-1 text-xs text-red-500">{errors.frequencyCount}</p>
            )}
          </div>

          <div className="rounded-xl border border-stone-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <label className="text-sm font-medium text-stone-700">提醒</label>
              <button
                type="button"
                onClick={() => setForm({ ...form, reminderEnabled: !form.reminderEnabled })}
                className={cn(
                  'relative inline-flex h-6 w-11 items-center rounded-full transition-colors duration-200',
                  form.reminderEnabled ? 'bg-emerald-500' : 'bg-stone-300'
                )}
              >
                <span
                  className={cn(
                    'inline-block h-4 w-4 transform rounded-full bg-white shadow-sm transition-transform duration-200',
                    form.reminderEnabled ? 'translate-x-6' : 'translate-x-1'
                  )}
                />
              </button>
            </div>

            {form.reminderEnabled && (
              <>
                <input
                  type="time"
                  value={form.reminderTime}
                  onChange={(e) => setForm({ ...form, reminderTime: e.target.value })}
                  className="w-full rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm text-stone-700 outline-none transition-colors focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
                />
                <div className="flex gap-1.5">
                  {WEEKDAY_LABELS.map((label, index) => {
                    const isSelected = form.reminderDays.includes(index)
                    return (
                      <button
                        key={index}
                        type="button"
                        onClick={() => toggleReminderDay(index)}
                        className={cn(
                          'flex-1 rounded-lg py-1.5 text-xs font-medium transition-all duration-200',
                          isSelected
                            ? 'bg-emerald-500 text-white shadow-sm'
                            : 'bg-stone-100 text-stone-500 hover:bg-stone-200'
                        )}
                      >
                        {label}
                      </button>
                    )
                  })}
                </div>
              </>
            )}
          </div>
        </div>

        <div className="flex gap-3 border-t border-stone-100 px-6 py-4">
          <button
            type="button"
            onClick={onClose}
            className="flex-1 rounded-xl border border-stone-200 bg-white px-4 py-2.5 text-sm font-medium text-stone-600 transition-colors hover:bg-stone-50"
          >
            取消
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            className="flex-1 rounded-xl bg-emerald-500 px-4 py-2.5 text-sm font-medium text-white transition-colors hover:bg-emerald-600"
          >
            {habitId ? '保存修改' : '创建习惯'}
          </button>
        </div>
      </div>
    </div>
  )
}
