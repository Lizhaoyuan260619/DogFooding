import type { Habit } from '@/types'

export async function requestNotificationPermission(): Promise<NotificationPermission> {
  if (!('Notification' in window)) {
    return 'denied'
  }
  if (Notification.permission === 'granted') {
    return 'granted'
  }
  if (Notification.permission !== 'denied') {
    return await Notification.requestPermission()
  }
  return Notification.permission
}

export function getNotificationPermission(): NotificationPermission {
  if (!('Notification' in window)) return 'denied'
  return Notification.permission
}

export function scheduleNotification(habit: Habit): void {
  if (!habit.reminderEnabled) return
  if (getNotificationPermission() !== 'granted') return

  const [hours, minutes] = habit.reminderTime.split(':').map(Number)
  if (isNaN(hours) || isNaN(minutes)) return

  const now = new Date()
  const scheduled = new Date()
  scheduled.setHours(hours, minutes, 0, 0)

  if (scheduled <= now) {
    scheduled.setDate(scheduled.getDate() + 1)
  }

  const delay = scheduled.getTime() - now.getTime()

  setTimeout(() => {
    const dayOfWeek = scheduled.getDay()
    if (habit.reminderDays.length > 0 && !habit.reminderDays.includes(dayOfWeek)) {
      scheduleNotification(habit)
      return
    }

    new Notification('习惯打卡提醒', {
      body: `别忘了完成今天的习惯：${habit.name}`,
      icon: '/favicon.svg',
      tag: habit.id,
    })

    scheduleNotification(habit)
  }, delay)
}

export function scheduleAllNotifications(habits: Habit[]): void {
  for (const habit of habits) {
    if (habit.reminderEnabled) {
      scheduleNotification(habit)
    }
  }
}
