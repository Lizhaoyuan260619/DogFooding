import { Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import { HABIT_COLORS } from '@/utils/constants'

interface ColorPickerProps {
  value: string
  onChange: (color: string) => void
}

export default function ColorPicker({ value, onChange }: ColorPickerProps) {
  return (
    <div className="grid grid-cols-5 gap-3">
      {HABIT_COLORS.map((color) => {
        const isSelected = value === color
        return (
          <button
            key={color}
            type="button"
            onClick={() => onChange(color)}
            className="flex items-center justify-center"
          >
            <span
              className={cn(
                'flex items-center justify-center w-8 h-8 rounded-full transition-all duration-200',
                isSelected ? 'ring-2 ring-offset-2 ring-emerald-500 scale-110' : 'hover:scale-110'
              )}
              style={{ backgroundColor: color }}
            >
              {isSelected && <Check size={14} className="text-white" strokeWidth={3} />}
            </span>
          </button>
        )
      })}
    </div>
  )
}
