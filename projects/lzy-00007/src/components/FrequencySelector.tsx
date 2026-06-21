import { cn } from '@/lib/utils'
import { WEEKDAY_LABELS } from '@/utils/constants'

interface FrequencySelectorProps {
  frequencyType: 'daily' | 'weekly' | 'monthly'
  frequencyCount: number
  reminderDays: number[]
  onTypeChange: (type: 'daily' | 'weekly' | 'monthly') => void
  onCountChange: (count: number) => void
  onReminderDaysChange: (days: number[]) => void
}

const TYPE_OPTIONS = [
  { value: 'daily' as const, label: '每天' },
  { value: 'weekly' as const, label: '每周' },
  { value: 'monthly' as const, label: '每月' },
]

const TYPE_LABELS: Record<string, string> = {
  daily: '每天',
  weekly: '每周',
  monthly: '每月',
}

export default function FrequencySelector({
  frequencyType,
  frequencyCount,
  reminderDays,
  onTypeChange,
  onCountChange,
  onReminderDaysChange,
}: FrequencySelectorProps) {
  const toggleDay = (day: number) => {
    if (reminderDays.includes(day)) {
      onReminderDaysChange(reminderDays.filter((d) => d !== day))
    } else {
      onReminderDaysChange([...reminderDays, day])
    }
  }

  return (
    <div className="space-y-3">
      <label className="text-sm font-medium text-stone-700">
        {TYPE_LABELS[frequencyType]} {frequencyCount} 次
      </label>

      <div className="flex items-center gap-3">
        <select
          value={frequencyType}
          onChange={(e) => onTypeChange(e.target.value as 'daily' | 'weekly' | 'monthly')}
          className="flex-1 rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-700 outline-none transition-colors focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
        >
          {TYPE_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>
              {opt.label}
            </option>
          ))}
        </select>

        <input
          type="number"
          min={1}
          max={frequencyType === 'daily' ? 1 : frequencyType === 'weekly' ? 7 : 31}
          value={frequencyCount}
          onChange={(e) => onCountChange(Math.max(1, parseInt(e.target.value) || 1))}
          className="w-20 rounded-xl border border-stone-200 bg-white px-3 py-2 text-sm text-stone-700 outline-none transition-colors focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
        />
        <span className="text-sm text-stone-500">次</span>
      </div>

      {frequencyType === 'weekly' && (
        <div className="flex gap-1.5">
          {WEEKDAY_LABELS.map((label, index) => {
            const isSelected = reminderDays.includes(index)
            return (
              <button
                key={index}
                type="button"
                onClick={() => toggleDay(index)}
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
      )}
    </div>
  )
}
