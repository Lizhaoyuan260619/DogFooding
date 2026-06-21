import { useState, useMemo, useRef, useCallback } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getYearDays, getHeatmapData, formatDate } from '@/utils/date'
import { HEATMAP_LEVELS } from '@/utils/constants'

function getLevel(count: number): number {
  if (count === 0) return 0
  if (count === 1) return 1
  if (count === 2) return 2
  if (count === 3) return 3
  if (count === 4) return 4
  return 5
}

const MONTH_LABELS = ['1月', '2月', '3月', '4月', '5月', '6月', '7月', '8月', '9月', '10月', '11月', '12月']
const DAY_LABELS = ['一', '', '三', '', '五', '', '日']

interface TooltipData {
  date: string
  count: number
  habits: string[]
  x: number
  y: number
}

export default function HeatmapCalendar() {
  const currentYear = new Date().getFullYear()
  const [year, setYear] = useState(currentYear)
  const [month, setMonth] = useState(new Date().getMonth())
  const [viewMode, setViewMode] = useState<'year' | 'month'>('year')
  const { checkIns, habits } = useAppStore()
  const [tooltip, setTooltip] = useState<TooltipData | null>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const yearOptions = [currentYear, currentYear - 1, currentYear - 2]

  const heatmapData = useMemo(() => getHeatmapData(year, checkIns), [year, checkIns])

  const grid = useMemo(() => {
    const days = getYearDays(year)
    const firstDay = days[0]
    const firstDayOfWeek = firstDay.getDay()
    const offset = firstDayOfWeek === 0 ? 6 : firstDayOfWeek - 1

    const weeks: (Date | null)[][] = []
    let currentWeek: (Date | null)[] = Array(offset).fill(null)

    for (const day of days) {
      const dow = day.getDay()
      const adjustedDow = dow === 0 ? 6 : dow - 1
      currentWeek.push(day)
      if (adjustedDow === 6) {
        weeks.push(currentWeek)
        currentWeek = []
      }
    }
    if (currentWeek.length > 0) {
      while (currentWeek.length < 7) currentWeek.push(null)
      weeks.push(currentWeek)
    }

    return weeks
  }, [year])

  const monthPositions = useMemo(() => {
    const positions: { label: string; weekIndex: number }[] = []
    let lastMonth = -1
    grid.forEach((week, weekIndex) => {
      for (const day of week) {
        if (day) {
          const m = day.getMonth()
          if (m !== lastMonth) {
            positions.push({ label: MONTH_LABELS[m], weekIndex })
            lastMonth = m
          }
          break
        }
      }
    })
    return positions
  }, [grid])

  const getHabitNamesForDate = useCallback((dateStr: string) => {
    return checkIns
      .filter(c => c.date === dateStr)
      .map(c => habits.find(h => h.id === c.habitId)?.name ?? '')
      .filter(Boolean)
  }, [checkIns, habits])

  const handleCellHover = useCallback((e: React.MouseEvent, dateStr: string | null) => {
    if (!dateStr) {
      setTooltip(null)
      return
    }
    const rect = e.currentTarget.getBoundingClientRect()
    const count = heatmapData[dateStr] ?? 0
    setTooltip({
      date: dateStr,
      count,
      habits: getHabitNamesForDate(dateStr),
      x: rect.left + rect.width / 2,
      y: rect.top,
    })
  }, [heatmapData, getHabitNamesForDate])

  const monthGrid = useMemo(() => {
    if (viewMode !== 'month') return []
    const firstDay = new Date(year, month, 1)
    const lastDay = new Date(year, month + 1, 0)
    const startOffset = firstDay.getDay() === 0 ? 6 : firstDay.getDay() - 1
    const daysInMonth = lastDay.getDate()
    const rows: (number | null)[][] = []
    let row: (number | null)[] = Array(startOffset).fill(null)
    for (let d = 1; d <= daysInMonth; d++) {
      row.push(d)
      if (row.length === 7) {
        rows.push(row)
        row = []
      }
    }
    if (row.length > 0) {
      while (row.length < 7) row.push(null)
      rows.push(row)
    }
    return rows
  }, [year, month, viewMode])

  const prevMonth = () => {
    if (month === 0) {
      setMonth(11)
      setYear(y => y - 1)
    } else {
      setMonth(m => m - 1)
    }
  }

  const nextMonth = () => {
    if (month === 11) {
      setMonth(0)
      setYear(y => y + 1)
    } else {
      setMonth(m => m + 1)
    }
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6" ref={containerRef}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-base font-semibold text-gray-800">
          {viewMode === 'year' ? '年度热力图' : `${year}年${MONTH_LABELS[month]}`}
        </h3>
        <div className="flex items-center gap-2">
          <div className="flex gap-1 bg-gray-100 rounded-lg p-0.5">
            <button
              onClick={() => setViewMode('month')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'month' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              月视图
            </button>
            <button
              onClick={() => setViewMode('year')}
              className={`px-3 py-1 rounded-md text-xs font-medium transition-colors ${
                viewMode === 'year' ? 'bg-white text-gray-800 shadow-sm' : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              年视图
            </button>
          </div>

          {viewMode === 'year' ? (
            <select
              value={year}
              onChange={e => setYear(Number(e.target.value))}
              className="text-sm border border-gray-200 rounded-lg px-3 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-400"
            >
              {yearOptions.map(y => (
                <option key={y} value={y}>{y}年</option>
              ))}
            </select>
          ) : (
            <div className="flex items-center gap-1">
              <button onClick={prevMonth} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500">
                <ChevronLeft size={16} />
              </button>
              <select
                value={month}
                onChange={e => setMonth(Number(e.target.value))}
                className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-400"
              >
                {MONTH_LABELS.map((label, i) => (
                  <option key={i} value={i}>{label}</option>
                ))}
              </select>
              <select
                value={year}
                onChange={e => setYear(Number(e.target.value))}
                className="text-sm border border-gray-200 rounded-lg px-2 py-1.5 text-gray-600 focus:outline-none focus:ring-2 focus:ring-emerald-400"
              >
                {yearOptions.map(y => (
                  <option key={y} value={y}>{y}年</option>
                ))}
              </select>
              <button onClick={nextMonth} className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors text-gray-500">
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </div>
      </div>

      {viewMode === 'year' ? (
        <div className="relative overflow-x-auto">
          <div className="inline-block min-w-fit">
            <div className="relative h-5 mb-1 ml-8">
              {monthPositions.map(({ label, weekIndex }) => (
                <span
                  key={label + weekIndex}
                  className="absolute text-[10px] text-gray-400 whitespace-nowrap"
                  style={{ left: weekIndex * 16 }}
                >
                  {label}
                </span>
              ))}
            </div>

            <div className="flex gap-0">
              <div className="flex flex-col mr-1">
                {DAY_LABELS.map((label, i) => (
                  <div key={i} className="h-[14px] flex items-center">
                    <span className="text-[10px] text-gray-400 w-6 text-right">{label}</span>
                  </div>
                ))}
              </div>

              <div className="flex gap-[2px]">
                {grid.map((week, col) => (
                  <div key={col} className="flex flex-col gap-[2px]">
                    {week.map((day, row) => {
                      if (!day) {
                        return <div key={row} className="w-[14px] h-[14px]" />
                      }
                      const dateStr = formatDate(day)
                      const count = heatmapData[dateStr] ?? 0
                      const level = getLevel(count)
                      return (
                        <div
                          key={row}
                          className={`w-[14px] h-[14px] rounded-[2px] cursor-pointer transition-opacity hover:opacity-80 ${HEATMAP_LEVELS[level]}`}
                          onMouseEnter={e => handleCellHover(e, dateStr)}
                          onMouseLeave={() => setTooltip(null)}
                        />
                      )
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="flex items-center gap-1.5 mt-3 text-[10px] text-gray-400">
            <span>少</span>
            {HEATMAP_LEVELS.map((cls, i) => (
              <div key={i} className={`w-[14px] h-[14px] rounded-[2px] ${cls}`} />
            ))}
            <span>多</span>
          </div>
        </div>
      ) : (
        <div>
          <div className="grid grid-cols-7 gap-1 mb-1">
            {['一', '二', '三', '四', '五', '六', '日'].map(d => (
              <div key={d} className="text-center text-xs text-gray-400 py-1">{d}</div>
            ))}
          </div>
          <div className="grid grid-cols-7 gap-1">
            {monthGrid.map((week, wi) =>
              week.map((day, di) => {
                if (!day) {
                  return <div key={`${wi}-${di}`} className="aspect-square rounded-lg" />
                }
                const dateStr = formatDate(new Date(year, month, day))
                const count = heatmapData[dateStr] ?? 0
                const level = getLevel(count)
                const isToday = dateStr === formatDate(new Date())
                return (
                  <div
                    key={`${wi}-${di}`}
                    className={`aspect-square rounded-lg cursor-pointer transition-all hover:scale-105 flex items-center justify-center text-xs font-medium ${
                      level === 0 ? 'bg-gray-50 text-gray-400' : `${HEATMAP_LEVELS[level]} ${level >= 3 ? 'text-white' : 'text-gray-600'}`
                    } ${isToday ? 'ring-2 ring-emerald-500 ring-offset-1' : ''}`}
                    onMouseEnter={e => handleCellHover(e, dateStr)}
                    onMouseLeave={() => setTooltip(null)}
                  >
                    {day}
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}

      {tooltip && (
        <div
          className="fixed z-50 bg-gray-800 text-white text-xs rounded-lg px-3 py-2 pointer-events-none shadow-lg max-w-[200px]"
          style={{
            left: tooltip.x,
            top: tooltip.y - 8,
            transform: 'translate(-50%, -100%)',
          }}
        >
          <p className="font-medium">{tooltip.date}</p>
          <p className="text-gray-300">
            {tooltip.count}次打卡
          </p>
          {tooltip.habits.length > 0 && (
            <div className="mt-1 border-t border-gray-600 pt-1">
              {tooltip.habits.map(name => (
                <p key={name} className="text-gray-300">· {name}</p>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
