import { useState } from 'react'
import CompletionChart from '@/components/CompletionChart'
import TrendChart from '@/components/TrendChart'
import CategoryChart from '@/components/CategoryChart'
import HabitRanking from '@/components/HabitRanking'
import ExportPanel from '@/components/ExportPanel'

type Period = 'week' | 'month' | 'year'

const TABS: { key: Period; label: string }[] = [
  { key: 'week', label: '本周' },
  { key: 'month', label: '本月' },
  { key: 'year', label: '本年' },
]

export default function Stats() {
  const [period, setPeriod] = useState<Period>('week')

  return (
    <div className="min-h-screen bg-[#FFFDF7] pb-24">
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-between">
          <h1 className="font-[Outfit] text-2xl font-bold text-zinc-800">数据统计</h1>
          <div className="flex gap-1 bg-white rounded-lg p-1 shadow-sm">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setPeriod(tab.key)}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-all duration-200 ${
                  period === tab.key
                    ? 'bg-emerald-500 text-white shadow-sm'
                    : 'text-zinc-500 hover:text-zinc-700 hover:bg-zinc-50'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <CompletionChart period={period} />
          <TrendChart period={period} />
          <CategoryChart />
          <HabitRanking />
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6">
          <h3 className="text-base font-semibold text-gray-800 mb-4">数据导出</h3>
          <ExportPanel />
        </div>
      </div>
    </div>
  )
}
