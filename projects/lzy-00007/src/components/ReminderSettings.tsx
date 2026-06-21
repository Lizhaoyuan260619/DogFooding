import { useAppStore } from '@/store/useAppStore'
import { WEEKDAY_LABELS } from '@/utils/constants'

export default function ReminderSettings() {
  const habits = useAppStore((s) => s.habits)
  const updateHabit = useAppStore((s) => s.updateHabit)

  const toggleReminder = (habitId: string, enabled: boolean) => {
    updateHabit(habitId, { reminderEnabled: enabled })
  }

  const updateTime = (habitId: string, time: string) => {
    updateHabit(habitId, { reminderTime: time })
  }

  const toggleDay = (habitId: string, day: number, currentDays: number[]) => {
    const newDays = currentDays.includes(day)
      ? currentDays.filter((d) => d !== day)
      : [...currentDays, day].sort()
    updateHabit(habitId, { reminderDays: newDays })
  }

  if (habits.length === 0) {
    return (
      <p className="text-sm text-zinc-400 text-center py-4">暂无习惯，请先添加习惯</p>
    )
  }

  return (
    <div className="space-y-3">
      {habits.map((habit) => (
        <div
          key={habit.id}
          className="border border-zinc-200 rounded-xl p-4 space-y-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: habit.color }}
              />
              <span className="text-sm font-medium text-zinc-800">{habit.name}</span>
            </div>
            <button
              onClick={() => toggleReminder(habit.id, !habit.reminderEnabled)}
              className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                habit.reminderEnabled ? 'bg-emerald-500' : 'bg-zinc-200'
              }`}
            >
              <span
                className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform shadow-sm ${
                  habit.reminderEnabled ? 'translate-x-6' : 'translate-x-1'
                }`}
              />
            </button>
          </div>

          <div
            className={`overflow-hidden transition-all duration-300 ${
              habit.reminderEnabled ? 'max-h-40 opacity-100' : 'max-h-0 opacity-0'
            }`}
          >
            <div className="space-y-3 pt-1">
              <div>
                <label className="text-xs font-medium text-zinc-500 mb-1 block">提醒时间</label>
                <input
                  type="time"
                  value={habit.reminderTime}
                  onChange={(e) => updateTime(habit.id, e.target.value)}
                  className="px-3 py-1.5 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="text-xs font-medium text-zinc-500 mb-1 block">提醒日</label>
                <div className="flex gap-1">
                  {WEEKDAY_LABELS.map((label, i) => (
                    <button
                      key={i}
                      onClick={() => toggleDay(habit.id, i, habit.reminderDays)}
                      className={`w-8 h-8 rounded-lg text-xs font-medium transition-colors ${
                        habit.reminderDays.includes(i)
                          ? 'bg-emerald-500 text-white'
                          : 'bg-zinc-100 text-zinc-500 hover:bg-zinc-200'
                      }`}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
