import React from 'react'
import { TrendingUp, Users, Heart, MessageCircle, Calendar } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import type { CircleStats } from '@/types'

const StatItem: React.FC<{
  icon: React.ElementType
  label: string
  value: number
  color: string
  suffix?: string
}> = ({ icon: Icon, label, value, color, suffix = '' }) => (
  <div className="flex items-center gap-3 p-4 bg-white rounded-xl shadow-sm">
    <div
      className="w-12 h-12 rounded-xl flex items-center justify-center"
      style={{ backgroundColor: color + '20', color }}
    >
      <Icon size={24} />
    </div>
    <div>
      <p className="text-2xl font-bold text-gray-800">
        {value.toLocaleString()}
        {suffix}
      </p>
      <p className="text-sm text-gray-500">{label}</p>
    </div>
  </div>
)

export default function CircleStatsCard() {
  const { getCircleStats, userProfile, userBadges } = useAppStore()
  const stats: CircleStats = getCircleStats()

  const expPercentage = (userProfile.exp / userProfile.expToNextLevel) * 100

  return (
    <div className="space-y-4">
      <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-6 text-white">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-4">
            <div className="relative">
              <img
                src={userProfile.avatar}
                alt={userProfile.name}
                className="w-16 h-16 rounded-full border-4 border-white/30 object-cover"
              />
              <div className="absolute -bottom-1 -right-1 bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-0.5 rounded-full">
                Lv.{userProfile.level}
              </div>
            </div>
            <div>
              <h3 className="text-xl font-bold">{userProfile.name}</h3>
              <p className="text-white/70 text-sm">{userProfile.bio}</p>
            </div>
          </div>
          <div className="text-right">
            <p className="text-3xl font-bold">{userBadges.length}</p>
            <p className="text-white/70 text-sm">已获得徽章</p>
          </div>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-white/70">经验值</span>
            <span>
              {userProfile.exp} / {userProfile.expToNextLevel}
            </span>
          </div>
          <div className="h-2 bg-white/20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white rounded-full transition-all duration-500 animate-progress-fill"
              style={{ width: `${expPercentage}%` }}
            />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        <StatItem
          icon={Calendar}
          label="本周打卡"
          value={stats.weeklyCheckIns}
          color="#10B981"
          suffix=" 次"
        />
        <StatItem
          icon={Calendar}
          label="本月打卡"
          value={stats.monthlyCheckIns}
          color="#3B82F6"
          suffix=" 次"
        />
        <StatItem
          icon={TrendingUp}
          label="圈子动态"
          value={stats.totalPosts}
          color="#8B5CF6"
          suffix=" 条"
        />
        <StatItem
          icon={Heart}
          label="获赞总数"
          value={stats.totalLikes}
          color="#EF4444"
        />
        <StatItem
          icon={MessageCircle}
          label="评论总数"
          value={stats.totalComments}
          color="#F59E0B"
        />
        <StatItem
          icon={Users}
          label="活跃用户"
          value={stats.activeUsers}
          color="#EC4899"
          suffix=" 人"
        />
      </div>
    </div>
  )
}
