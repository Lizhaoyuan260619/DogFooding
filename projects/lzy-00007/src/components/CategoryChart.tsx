import { useMemo } from 'react'
import { Chart as ChartJS, ArcElement, Tooltip, Legend } from 'chart.js'
import { Doughnut } from 'react-chartjs-2'
import { useAppStore } from '@/store/useAppStore'

ChartJS.register(ArcElement, Tooltip, Legend)

export default function CategoryChart() {
  const { habits, checkIns, categories } = useAppStore()

  const data = useMemo(() => {
    const categoryCounts: Record<string, number> = {}

    for (const cat of categories) {
      categoryCounts[cat.id] = 0
    }

    for (const ci of checkIns) {
      const habit = habits.find(h => h.id === ci.habitId)
      if (habit) {
        categoryCounts[habit.category] = (categoryCounts[habit.category] ?? 0) + 1
      }
    }

    const activeCategories = categories.filter(c => (categoryCounts[c.id] ?? 0) > 0)

    return {
      labels: activeCategories.map(c => c.name),
      datasets: [
        {
          data: activeCategories.map(c => categoryCounts[c.id] ?? 0),
          backgroundColor: activeCategories.map(c => c.color + '80'),
          borderColor: activeCategories.map(c => c.color),
          borderWidth: 2,
          hoverOffset: 8,
        },
      ],
    }
  }, [habits, checkIns, categories])

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '55%',
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
        callbacks: {
          label: (ctx: { parsed: number; label: string; dataset: { data: number[] } }) => {
            const total = ctx.dataset.data.reduce((a: number, b: number) => a + b, 0)
            const pct = total > 0 ? Math.round((ctx.parsed / total) * 100) : 0
            return `${ctx.label}: ${ctx.parsed}次 (${pct}%)`
          },
        },
      },
    },
  }

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      <h3 className="text-base font-semibold text-gray-800 mb-4">分类分布</h3>
      <div className="h-64">
        {data.labels.length > 0 ? (
          <Doughnut data={data} options={options} />
        ) : (
          <div className="h-full flex items-center justify-center text-gray-400 text-sm">
            暂无打卡数据
          </div>
        )}
      </div>
    </div>
  )
}
