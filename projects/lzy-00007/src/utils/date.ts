import { format, subDays, startOfWeek, endOfWeek, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, parseISO, differenceInDays } from 'date-fns'
import type { CheckIn, Habit } from '@/types'

export function getToday(): string {
  return format(new Date(), 'yyyy-MM-dd')
}

export function formatDate(date: Date | string, fmt: string = 'yyyy-MM-dd'): string {
  const d = typeof date === 'string' ? parseISO(date) : date
  return format(d, fmt)
}

export function getWeekDays(date: Date = new Date()): Date[] {
  const start = startOfWeek(date, { weekStartsOn: 1 })
  const end = endOfWeek(date, { weekStartsOn: 1 })
  return eachDayOfInterval({ start, end })
}

export function getMonthDays(year: number, month: number): Date[] {
  const start = startOfMonth(new Date(year, month))
  const end = endOfMonth(new Date(year, month))
  return eachDayOfInterval({ start, end })
}

export function getYearDays(year: number): Date[] {
  const start = new Date(year, 0, 1)
  const end = new Date(year, 11, 31)
  return eachDayOfInterval({ start, end })
}

export function getStreak(habitId: string, checkIns: CheckIn[]): number {
  const habitCheckIns = checkIns
    .filter(c => c.habitId === habitId)
    .map(c => c.date)
    .sort()
    .reverse()

  if (habitCheckIns.length === 0) return 0

  const today = getToday()
  const yesterday = formatDate(subDays(new Date(), 1))

  if (habitCheckIns[0] !== today && habitCheckIns[0] !== yesterday) return 0

  let streak = 1
  for (let i = 0; i < habitCheckIns.length - 1; i++) {
    const curr = parseISO(habitCheckIns[i])
    const prev = parseISO(habitCheckIns[i + 1])
    if (differenceInDays(curr, prev) === 1) {
      streak++
    } else {
      break
    }
  }
  return streak
}

export function getTotalCheckIns(habitId: string, checkIns: CheckIn[]): number {
  return checkIns.filter(c => c.habitId === habitId).length
}

export function isCheckedIn(habitId: string, date: string, checkIns: CheckIn[]): boolean {
  return checkIns.some(c => c.habitId === habitId && c.date === date)
}

export function getCheckInsByDate(date: string, checkIns: CheckIn[]): CheckIn[] {
  return checkIns.filter(c => c.date === date)
}

export function getCheckInsByDateRange(start: string, end: string, checkIns: CheckIn[]): CheckIn[] {
  const startDate = parseISO(start)
  const endDate = parseISO(end)
  return checkIns.filter(c => {
    const d = parseISO(c.date)
    return d >= startDate && d <= endDate
  })
}

export function getCompletionRate(habit: Habit, checkIns: CheckIn[], startDate: string, endDate: string): number {
  const start = parseISO(startDate)
  const end = parseISO(endDate)
  const totalDays = differenceInDays(end, start) + 1
  if (totalDays <= 0) return 0

  const habitCheckIns = checkIns.filter(c => {
    if (c.habitId !== habit.id) return false
    const d = parseISO(c.date)
    return d >= start && d <= end
  })

  const uniqueDays = new Set(habitCheckIns.map(c => c.date)).size

  if (habit.frequencyType === 'daily') {
    return Math.min(100, (uniqueDays / totalDays) * 100)
  } else if (habit.frequencyType === 'weekly') {
    const weeks = Math.ceil(totalDays / 7)
    const expected = weeks * habit.frequencyCount
    return Math.min(100, (uniqueDays / Math.max(1, expected)) * 100)
  } else {
    const months = Math.ceil(totalDays / 30)
    const expected = months * habit.frequencyCount
    return Math.min(100, (uniqueDays / Math.max(1, expected)) * 100)
  }
}

export function getLast7DaysStatus(habitId: string, checkIns: CheckIn[]): { date: string; completed: boolean }[] {
  const today = new Date()
  const result = []
  for (let i = 6; i >= 0; i--) {
    const d = subDays(today, i)
    const dateStr = formatDate(d)
    result.push({
      date: dateStr,
      completed: isCheckedIn(habitId, dateStr, checkIns),
    })
  }
  return result
}

export function getHeatmapData(year: number, checkIns: CheckIn[]): Record<string, number> {
  const data: Record<string, number> = {}
  const days = getYearDays(year)
  for (const day of days) {
    const dateStr = formatDate(day)
    const count = getCheckInsByDate(dateStr, checkIns).length
    data[dateStr] = count
  }
  return data
}

export function isSameDateStr(d1: Date, d2: string): boolean {
  return isSameDay(d1, parseISO(d2))
}

export function generateId(): string {
  return Date.now().toString(36) + Math.random().toString(36).substring(2, 9)
}
