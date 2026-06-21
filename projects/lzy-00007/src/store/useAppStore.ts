import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type { Habit, CheckIn, Category } from '@/types'
import { DEFAULT_CATEGORIES } from '@/utils/constants'
import { generateId, getToday } from '@/utils/date'

interface AppStore {
  habits: Habit[]
  checkIns: CheckIn[]
  categories: Category[]
  initialized: boolean

  addHabit: (habit: Omit<Habit, 'id' | 'createdAt' | 'updatedAt'>) => void
  updateHabit: (id: string, updates: Partial<Habit>) => void
  deleteHabit: (id: string) => void

  checkIn: (habitId: string, date: string) => void
  uncheckIn: (habitId: string, date: string) => void

  addCategory: (category: Omit<Category, 'id'>) => void
  deleteCategory: (id: string) => void

  initDemoData: () => void
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      habits: [],
      checkIns: [],
      categories: DEFAULT_CATEGORIES,
      initialized: false,

      addHabit: (habitData) => {
        const now = new Date().toISOString()
        const habit: Habit = {
          ...habitData,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        }
        set((state) => ({ habits: [...state.habits, habit] }))
      },

      updateHabit: (id, updates) => {
        set((state) => ({
          habits: state.habits.map((h) =>
            h.id === id ? { ...h, ...updates, updatedAt: new Date().toISOString() } : h
          ),
        }))
      },

      deleteHabit: (id) => {
        set((state) => ({
          habits: state.habits.filter((h) => h.id !== id),
          checkIns: state.checkIns.filter((c) => c.habitId !== id),
        }))
      },

      checkIn: (habitId, date) => {
        const exists = get().checkIns.some(
          (c) => c.habitId === habitId && c.date === date
        )
        if (exists) return
        const checkIn: CheckIn = {
          id: generateId(),
          habitId,
          date,
          createdAt: new Date().toISOString(),
        }
        set((state) => ({ checkIns: [...state.checkIns, checkIn] }))
      },

      uncheckIn: (habitId, date) => {
        set((state) => ({
          checkIns: state.checkIns.filter(
            (c) => !(c.habitId === habitId && c.date === date)
          ),
        }))
      },

      addCategory: (categoryData) => {
        const category: Category = {
          ...categoryData,
          id: generateId(),
        }
        set((state) => ({ categories: [...state.categories, category] }))
      },

      deleteCategory: (id) => {
        set((state) => ({
          categories: state.categories.filter((c) => c.id !== id),
        }))
      },

      initDemoData: () => {
        if (get().initialized) return
        const now = new Date().toISOString()
        const today = getToday()

        const demoHabits: Habit[] = [
          {
            id: 'demo-1',
            name: '晨跑30分钟',
            icon: 'Dumbbell',
            color: '#F97316',
            category: 'fitness',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [1, 2, 3, 4, 5],
            reminderTime: '07:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-2',
            name: '阅读1小时',
            icon: 'BookOpen',
            color: '#3B82F6',
            category: 'learning',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [],
            reminderTime: '21:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-3',
            name: '冥想15分钟',
            icon: 'Brain',
            color: '#8B5CF6',
            category: 'mindfulness',
            frequencyType: 'weekly',
            frequencyCount: 3,
            reminderDays: [1, 3, 5],
            reminderTime: '08:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-4',
            name: '喝8杯水',
            icon: 'Droplets',
            color: '#10B981',
            category: 'health',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [],
            reminderTime: '09:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-5',
            name: '写日记',
            icon: 'Pencil',
            color: '#EC4899',
            category: 'creative',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [],
            reminderTime: '22:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
        ]

        const demoCheckIns: CheckIn[] = []
        for (let i = 30; i >= 0; i--) {
          const d = new Date()
          d.setDate(d.getDate() - i)
          const dateStr = d.toISOString().split('T')[0]

          for (const habit of demoHabits) {
            const shouldCheckIn = Math.random() > (habit.frequencyType === 'weekly' ? 0.5 : 0.2)
            if (shouldCheckIn && dateStr !== today) {
              demoCheckIns.push({
                id: generateId() + i + habit.id,
                habitId: habit.id,
                date: dateStr,
                createdAt: d.toISOString(),
              })
            }
          }
        }

        set({
          habits: demoHabits,
          checkIns: demoCheckIns,
          initialized: true,
        })
      },
    }),
    {
      name: 'habit-tracker-storage',
    }
  )
)
