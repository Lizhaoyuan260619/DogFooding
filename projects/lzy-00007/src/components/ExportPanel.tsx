import { useState } from 'react'
import { Download, Check, FileJson, FileSpreadsheet } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { exportToJSON, exportToCSV, downloadFile } from '@/utils/export'

type ExportFormat = 'csv' | 'json'

export default function ExportPanel() {
  const habits = useAppStore((s) => s.habits)
  const checkIns = useAppStore((s) => s.checkIns)

  const [format, setFormat] = useState<ExportFormat>('csv')
  const [selectedHabits, setSelectedHabits] = useState<string[]>([])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [exporting, setExporting] = useState(false)
  const [progress, setProgress] = useState(0)
  const [success, setSuccess] = useState(false)

  const allSelected = habits.length > 0 && selectedHabits.length === habits.length

  const toggleAll = () => {
    setSelectedHabits(allSelected ? [] : habits.map((h) => h.id))
  }

  const toggleHabit = (id: string) => {
    setSelectedHabits((prev) =>
      prev.includes(id) ? prev.filter((h) => h !== id) : [...prev, id]
    )
  }

  const handleExport = () => {
    setExporting(true)
    setProgress(0)
    setSuccess(false)

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval)
          return 100
        }
        return prev + 10
      })
    }, 100)

    setTimeout(() => {
      clearInterval(interval)
      setProgress(100)

      const selected = selectedHabits.length > 0 ? selectedHabits : undefined
      const start = startDate || undefined
      const end = endDate || undefined

      if (format === 'json') {
        const content = exportToJSON(habits, checkIns, selected, start, end)
        downloadFile(content, `habits-export-${new Date().toISOString().split('T')[0]}.json`, 'application/json')
      } else {
        const content = exportToCSV(habits, checkIns, selected, start, end)
        downloadFile(content, `habits-export-${new Date().toISOString().split('T')[0]}.csv`, 'text/csv')
      }

      setExporting(false)
      setSuccess(true)
      setTimeout(() => setSuccess(false), 3000)
    }, 1000)
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <button
          onClick={() => setFormat('csv')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            format === 'csv'
              ? 'bg-emerald-500 text-white'
              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
          }`}
        >
          <FileSpreadsheet className="w-4 h-4" />
          CSV
        </button>
        <button
          onClick={() => setFormat('json')}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            format === 'json'
              ? 'bg-emerald-500 text-white'
              : 'bg-zinc-100 text-zinc-600 hover:bg-zinc-200'
          }`}
        >
          <FileJson className="w-4 h-4" />
          JSON
        </button>
      </div>

      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-zinc-700">选择习惯</span>
          <button
            onClick={toggleAll}
            className="text-xs text-emerald-600 hover:text-emerald-700 font-medium"
          >
            {allSelected ? '取消全选' : '全选'}
          </button>
        </div>
        <div className="max-h-40 overflow-y-auto space-y-1 rounded-lg border border-zinc-200 p-2">
          {habits.length === 0 && (
            <p className="text-xs text-zinc-400 py-2 text-center">暂无习惯</p>
          )}
          {habits.map((habit) => (
            <label
              key={habit.id}
              className="flex items-center gap-2 py-1 px-2 rounded hover:bg-zinc-50 cursor-pointer"
            >
              <input
                type="checkbox"
                checked={selectedHabits.includes(habit.id)}
                onChange={() => toggleHabit(habit.id)}
                className="w-4 h-4 rounded border-zinc-300 text-emerald-500 focus:ring-emerald-500"
              />
              <span
                className="w-3 h-3 rounded-full flex-shrink-0"
                style={{ backgroundColor: habit.color }}
              />
              <span className="text-sm text-zinc-700">{habit.name}</span>
            </label>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="text-sm font-medium text-zinc-700 mb-1 block">开始日期</label>
          <input
            type="date"
            value={startDate}
            onChange={(e) => setStartDate(e.target.value)}
            className="w-full px-3 py-2 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>
        <div>
          <label className="text-sm font-medium text-zinc-700 mb-1 block">结束日期</label>
          <input
            type="date"
            value={endDate}
            onChange={(e) => setEndDate(e.target.value)}
            className="w-full px-3 py-2 border border-zinc-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-500"
          />
        </div>
      </div>

      {exporting && (
        <div className="space-y-1">
          <div className="h-2 bg-zinc-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-emerald-500 rounded-full transition-all duration-100"
              style={{ width: `${progress}%` }}
            />
          </div>
          <p className="text-xs text-zinc-500 text-center">正在导出...</p>
        </div>
      )}

      {success && (
        <div className="flex items-center gap-2 p-3 bg-emerald-50 text-emerald-700 rounded-lg text-sm">
          <Check className="w-4 h-4" />
          导出成功！
        </div>
      )}

      <button
        onClick={handleExport}
        disabled={exporting}
        className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-emerald-500 text-white rounded-lg text-sm font-medium hover:bg-emerald-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <Download className="w-4 h-4" />
        导出数据
      </button>
    </div>
  )
}
