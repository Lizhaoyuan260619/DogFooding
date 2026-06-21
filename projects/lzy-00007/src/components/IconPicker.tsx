import {
  Dumbbell,
  BookOpen,
  Droplets,
  Moon,
  Apple,
  Brain,
  Heart,
  FootprintsIcon,
  Music,
  Pencil,
  Flame,
  Sun,
  Coffee,
  Bike,
  Palette,
  Code,
  Leaf,
  Zap,
  Star,
  Trophy,
  Target,
  Smile,
  Clock,
  TrendingUp,
  Pilcrow,
  Ear,
  Eye,
  Hand,
  Shield,
  Wind,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'
import { cn } from '@/lib/utils'
import { HABIT_ICONS } from '@/utils/constants'

const ICON_MAP: Record<string, LucideIcon> = {
  Dumbbell,
  BookOpen,
  Droplets,
  Moon,
  Apple,
  Brain,
  Heart,
  FootprintsIcon,
  Music,
  Pencil,
  Flame,
  Sun,
  Coffee,
  Bike,
  Palette,
  Code,
  Leaf,
  Zap,
  Star,
  Trophy,
  Target,
  Smile,
  Clock,
  TrendingUp,
  Pilcrow,
  Ear,
  Eye,
  Hand,
  Shield,
  Wind,
}

interface IconPickerProps {
  value: string
  onChange: (icon: string) => void
}

export default function IconPicker({ value, onChange }: IconPickerProps) {
  return (
    <div className="grid grid-cols-6 gap-2">
      {HABIT_ICONS.map((iconName) => {
        const IconComponent = ICON_MAP[iconName]
        if (!IconComponent) return null
        const isSelected = value === iconName
        return (
          <button
            key={iconName}
            type="button"
            onClick={() => onChange(iconName)}
            className={cn(
              'flex items-center justify-center rounded-xl p-2.5 transition-all duration-200',
              isSelected
                ? 'bg-emerald-50 ring-2 ring-emerald-500 text-emerald-600'
                : 'bg-stone-50 text-stone-500 hover:bg-stone-100 hover:text-stone-700'
            )}
          >
            <IconComponent size={20} />
          </button>
        )
      })}
    </div>
  )
}
