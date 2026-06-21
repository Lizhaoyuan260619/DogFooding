import type { Category } from '@/types'

export const HABIT_ICONS = [
  'Dumbbell', 'BookOpen', 'Droplets', 'Moon', 'Apple', 'Brain',
  'Heart', 'FootprintsIcon', 'Music', 'Pencil', 'Flame', 'Sun',
  'Coffee', 'Bike', 'Palette', 'Code', 'Leaf', 'Zap',
  'Star', 'Trophy', 'Target', 'Smile', 'Clock', 'TrendingUp',
  'Pilcrow', 'Ear', 'Eye', 'Hand', 'Shield', 'Wind',
]

export const HABIT_COLORS = [
  '#10B981', '#F59E0B', '#EF4444', '#3B82F6', '#8B5CF6',
  '#EC4899', '#F97316', '#14B8A6', '#6366F1', '#84CC16',
  '#06B6D4', '#D946EF', '#E11D48', '#65A30D', '#7C3AED',
  '#DB2777', '#0891B2', '#CA8A04', '#DC2626', '#4F46E5',
]

export const DEFAULT_CATEGORIES: Category[] = [
  { id: 'health', name: '健康', icon: 'Heart', color: '#EF4444' },
  { id: 'fitness', name: '运动', icon: 'Dumbbell', color: '#F97316' },
  { id: 'learning', name: '学习', icon: 'BookOpen', color: '#3B82F6' },
  { id: 'lifestyle', name: '生活', icon: 'Coffee', color: '#10B981' },
  { id: 'mindfulness', name: '冥想', icon: 'Brain', color: '#8B5CF6' },
  { id: 'creative', name: '创意', icon: 'Palette', color: '#EC4899' },
  { id: 'social', name: '社交', icon: 'Smile', color: '#14B8A6' },
  { id: 'finance', name: '理财', icon: 'TrendingUp', color: '#F59E0B' },
]

export const WEEKDAY_LABELS = ['日', '一', '二', '三', '四', '五', '六']

export const HEATMAP_LEVELS = [
  'bg-zinc-100',
  'bg-emerald-100',
  'bg-emerald-300',
  'bg-emerald-500',
  'bg-emerald-700',
  'bg-emerald-900',
]
