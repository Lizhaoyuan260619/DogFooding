import { useMemo } from 'react'
import { Chart as ChartJS, PointElement, LineElement, CategoryScale, LinearScale, Title, Tooltip, Legend, Filler } from 'chart.js'
import type { TooltipItem } from 'chart.js'
import { Line } from 'react-chartjs-2'
import { useAppStore } from '@/store/useAppStore'
import { formatDate } from '@/utils/date'
import { subDays } from 'date-fns'

ChartJS.register(PointElement, LineElement, CategoryScale, LinearScale, Title, Tooltip, Legend, Filler)

interface TrendChartProps {
  period: 'week' | 'month' | 'year'
}

export default function TrendChart({ period }: TrendChartProps) {
  const { habits, checkIns } = useAppStore()

  const data = useMemo(() => {
    const today = new Date()
    const days = period === 'week' ? 7 : period === 'month' ? 30 : 365

    const dateLabels: string[] = []
    for (let i = days - 1; i >= 0; i--) {
      dateLabels.push(formatDate(subDays(today, i)))
    }

    const displayLabels = dateLabels.map(d => {
      const date = new Date(d)
      return `${date.getMonth() + 1}/${date.getDate()}`
    })

    const datasets = habits.map(habit => {
      const dailyCounts: number[] = []
      const habitCheckInDates = new Set(
        checkIns.filter(c => c.habitId === habit.id).map(c => c.date)
      )

      for (const dateStr of dateLabels) {
        dailyCounts.push(habitCheckInDates.has(dateStr) ? 1 : 0)
      }

      return {
        label: habit.name,
        data: dailyCounts,
        borderColor: habit.color,
        backgroundColor: habit.color + '20',
        fill: true,
        tension: 0.4,
        pointRadius: period === 'week' ? 5 : period === 'month' ? 2 : 0,
        pointHoverRadius: 6,
        pointBackgroundColor: habit.color,
        pointBorderColor: '#fff',
        pointBorderWidth: period === 'week' ? 2 : 0,
        borderWidth: 2,
      }
    })

    return {
      labels: displayLabels,
      datasets,
    }
  }, [habits, checkIns, period])

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: {
      mode: 'index' as const,
      intersect: false,
    },
    plugins: {
      legend: {
        position: 'bottom' as const,
        labels: {
          usePointStyle: true,
          padding: 16,
          font: { size: 11 },
        },
      },
      title: { display: false },
      tooltip: {
        mode: 'index' as const,
        intersect: false,
        backgroundColor: 'rgba(0,0,0,0.8)',
        titleFont: { size: 12 },
        bodyFont: { size: 11 },
        padding: 10,
        cornerRadius: 8,
        callbacks: {
          label: (ctx: TooltipItem<'line'>) => {
            return `${ctx.dataset.label}: ${ctx.parsed.y ? '✓ 已完成' : '○ 未完成'}`
          },
        },
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        max: 1,
        ticks: {
          stepSize: 1,
          callback: (value: string | number) => value === 1 ? '完成' : value === 0 ? '未完成' : '',
          font: { size: 10 },
        },
        grid: { color: '#f3f4f6' },
        title: {
          display: true,
          text: '完成状态',
          font: { size: 11 },
        },
      },
      x: {
        grid: { display: false },
        ticks: {
          maxTicksLimit: period === 'week' ? 7 : period === 'month' ? 10 : 12,
          font: { size: 10 },
        },
      },
    },
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">
        打卡趋势
        <span className="text-sm font-normal text-gray-400 ml-2">
          {period === 'week' ? '近7天' : period === 'month' ? '近30天' : '近一年'}
        </span>
      </h3>
      <div className="h-64">
        {habits.length > 0 ? (
          <Line data={data} options={options} />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400 text-sm">
            暂无习惯数据
          </div>
        )}
      </div>
    </div>
  )
}
