import { useMemo } from 'react'
import { Chart as ChartJS, CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend } from 'chart.js'
import { Bar } from 'react-chartjs-2'
import { useAppStore } from '@/store/useAppStore'
import { getCompletionRate, formatDate } from '@/utils/date'
import { subDays } from 'date-fns'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

interface CompletionChartProps {
  period: 'week' | 'month' | 'year'
}

export default function CompletionChart({ period }: CompletionChartProps) {
  const { habits, checkIns } = useAppStore()

  const { labels, rates } = useMemo(() => {
    const today = new Date()
    let start: Date
    if (period === 'week') {
      start = subDays(today, 6)
    } else if (period === 'month') {
      start = subDays(today, 29)
    } else {
      start = subDays(today, 364)
    }

    const startDate = formatDate(start)
    const endDate = formatDate(today)

    const labels = habits.map(h => h.name)
    const rates = habits.map(h => {
      const r = getCompletionRate(h, checkIns, startDate, endDate)
      return Math.round(r * 10) / 10
    })

    return { labels, rates }
  }, [habits, checkIns, period])

  const data = {
    labels,
    datasets: [
      {
        label: '完成率 (%)',
        data: rates,
        backgroundColor: habits.map(h => {
          const rate = rates[habits.indexOf(h)] ?? 0
          if (rate >= 80) return h.color + 'CC'
          if (rate >= 50) return h.color + '99'
          return h.color + '66'
        }),
        borderColor: habits.map(h => h.color),
        borderWidth: 1,
        borderRadius: 6,
        borderSkipped: false,
      },
    ],
  }

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: { display: false },
      title: { display: false },
      tooltip: {
        backgroundColor: 'rgba(0,0,0,0.8)',
        titleFont: { size: 12 },
        bodyFont: { size: 11 },
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (ctx: { parsed: { y: number } }) => {
            const rate = ctx.parsed.y
            const label = rate >= 80 ? ' 🎯 优秀' : rate >= 50 ? ' 👍 良好' : ' 💪 加油'
            return `完成率: ${rate}%${label}`
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 100,
        ticks: {
          callback: (value: number | string) => `${value}%`,
          font: { size: 10 },
        },
        grid: { color: '#f3f4f6' },
      },
      x: {
        grid: { display: false },
        ticks: {
          maxRotation: 45,
          font: { size: 11 },
        },
      },
    },
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        完成率统计
        <span className="text-sm font-normal text-gray-400 ml-2">
          {period === 'week' ? '近7天' : period === 'month' ? '近30天' : '近一年'}
        </span>
      </h3>
      <div className="h-64">
        {habits.length > 0 ? (
          <Bar data={data} options={options} />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400 text-sm">
            暂无习惯数据
          </div>
        )}
      </div>
    </div>
  )
}
