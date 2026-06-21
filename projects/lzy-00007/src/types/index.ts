export interface Habit {
  id: string
  name: string
  icon: string
  color: string
  category: string
  frequencyType: 'daily' | 'weekly' | 'monthly'
  frequencyCount: number
  reminderDays: number[]
  reminderTime: string
  reminderEnabled: boolean
  createdAt: string
  updatedAt: string
}

export interface CheckIn {
  id: string
  habitId: string
  date: string
  createdAt: string
}

export interface Category {
  id: string
  name: string
  icon: string
  color: string
}

export interface HabitFormData {
  name: string
  icon: string
  color: string
  category: string
  frequencyType: 'daily' | 'weekly' | 'monthly'
  frequencyCount: number
  reminderDays: number[]
  reminderTime: string
  reminderEnabled: boolean
}

export interface FormErrors {
  name?: string
  category?: string
  frequencyCount?: string
  reminderTime?: string
}
