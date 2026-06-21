import type { Habit, CheckIn } from '@/types'

export function exportToJSON(
  habits: Habit[],
  checkIns: CheckIn[],
  selectedHabits?: string[],
  startDate?: string,
  endDate?: string
): string {
  let filteredCheckIns = checkIns
  if (selectedHabits && selectedHabits.length > 0) {
    filteredCheckIns = filteredCheckIns.filter(c => selectedHabits.includes(c.habitId))
  }
  if (startDate) {
    filteredCheckIns = filteredCheckIns.filter(c => c.date >= startDate)
  }
  if (endDate) {
    filteredCheckIns = filteredCheckIns.filter(c => c.date <= endDate)
  }

  let filteredHabits = habits
  if (selectedHabits && selectedHabits.length > 0) {
    filteredHabits = habits.filter(h => selectedHabits.includes(h.id))
  }

  return JSON.stringify({
    exportedAt: new Date().toISOString(),
    habits: filteredHabits,
    checkIns: filteredCheckIns,
  }, null, 2)
}

export function exportToCSV(
  habits: Habit[],
  checkIns: CheckIn[],
  selectedHabits?: string[],
  startDate?: string,
  endDate?: string
): string {
  let filteredCheckIns = checkIns
  if (selectedHabits && selectedHabits.length > 0) {
    filteredCheckIns = filteredCheckIns.filter(c => selectedHabits.includes(c.habitId))
  }
  if (startDate) {
    filteredCheckIns = filteredCheckIns.filter(c => c.date >= startDate)
  }
  if (endDate) {
    filteredCheckIns = filteredCheckIns.filter(c => c.date <= endDate)
  }

  let filteredHabits = habits
  if (selectedHabits && selectedHabits.length > 0) {
    filteredHabits = habits.filter(h => selectedHabits.includes(h.id))
  }

  const habitMap = new Map(habits.map(h => [h.id, h.name]))

  const lines: string[] = ['日期,习惯名称,习惯分类,打卡时间']

  for (const ci of filteredCheckIns.sort((a, b) => a.date.localeCompare(b.date))) {
    const habit = filteredHabits.find(h => h.id === ci.habitId)
    if (!habit) continue
    lines.push(`${ci.date},"${habitMap.get(ci.habitId) || ci.habitId}","${habit.category}","${ci.createdAt}"`)
  }

  return lines.join('\n')
}

export function downloadFile(content: string, filename: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}
