import React, { useState, useMemo } from 'react'
import { Trophy, Filter, Award, Flame, Target, Users, Compass, Sparkles } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import BadgeCard from '@/components/BadgeCard'
import CircleStatsCard from '@/components/CircleStatsCard'
import type { BadgeCategory, BadgeRarity } from '@/types'
import { BADGE_CATEGORY_NAMES, BADGE_RARITY_COLORS } from '@/utils/constants'

const categoryIcons: Record<BadgeCategory, React.ElementType> = {
  streak: Flame,
  milestone: Target,
  social: Users,
  explorer: Compass,
  special: Sparkles,
}

const rarityOrder: BadgeRarity[] = ['bronze', 'silver', 'gold', 'platinum', 'legendary']
const categoryOrder: BadgeCategory[] = ['streak', 'milestone', 'explorer', 'social', 'special']

export default function Achievements() {
  const { badges, userBadges } = useAppStore()
  const [selectedCategory, setSelectedCategory] = useState<BadgeCategory | 'all'>('all')
  const [filterUnlocked, setFilterUnlocked] = useState<'all' | 'unlocked' | 'locked'>('all')

  const unlockedCount = userBadges.length
  const totalCount = badges.length
  const progressPercentage = Math.round((unlockedCount / totalCount) * 100)

  const filteredBadges = useMemo(() => {
    return badges.filter((badge) => {
      const isUnlocked = userBadges.some((ub) => ub.badgeId === badge.id)

      if (selectedCategory !== 'all' && badge.category !== selectedCategory) {
        return false
      }

      if (filterUnlocked === 'unlocked' && !isUnlocked) {
        return false
      }

      if (filterUnlocked === 'locked' && isUnlocked) {
        return false
      }

      return true
    })
  }, [badges, userBadges, selectedCategory, filterUnlocked])

  const badgesByCategory = useMemo(() => {
    const grouped: Record<BadgeCategory, typeof badges> = {
      streak: [],
      milestone: [],
      social: [],
      explorer: [],
      special: [],
    }

    filteredBadges.forEach((badge) => {
      grouped[badge.category].push(badge)
    })

    return grouped
  }, [filteredBadges])

  const rarityLabels: Record<BadgeRarity, string> = {
    bronze: '青铜',
    silver: '白银',
    gold: '黄金',
    platinum: '铂金',
    legendary: '传奇',
  }

  const getRarityCount = (rarity: BadgeRarity) => {
    return badges.filter((b) => b.rarity === rarity).length
  }

  const getRarityUnlockedCount = (rarity: BadgeRarity) => {
    return userBadges.filter((ub) => {
      const badge = badges.find((b) => b.id === ub.badgeId)
      return badge?.rarity === rarity
    }).length
  }

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Trophy className="text-yellow-500" />
            成就中心
          </h1>
          <p className="text-gray-500 mt-1">解锁徽章，记录成长的每一步</p>
        </div>
      </div>

      <div className="mb-8">
        <CircleStatsCard />
      </div>

      <div className="bg-white rounded-2xl shadow-sm p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
          <div className="flex items-center gap-4">
            <div className="relative w-20 h-20">
              <svg className="w-20 h-20 transform -rotate-90">
                <circle
                  cx="40"
                  cy="40"
                  r="35"
                  fill="none"
                  stroke="#E5E7EB"
                  strokeWidth="6"
                />
                <circle
                  cx="40"
                  cy="40"
                  r="35"
                  fill="none"
                  stroke="url(#gradient)"
                  strokeWidth="6"
                  strokeLinecap="round"
                  strokeDasharray={`${progressPercentage * 2.2} 220`}
                  className="transition-all duration-1000"
                />
                <defs>
                  <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" stopColor="#3B82F6" />
                    <stop offset="100%" stopColor="#8B5CF6" />
                  </linearGradient>
                </defs>
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xl font-bold text-gray-800">{progressPercentage}%</span>
              </div>
            </div>
            <div>
              <p className="text-3xl font-bold text-gray-800">
                {unlockedCount} <span className="text-lg text-gray-400">/ {totalCount}</span>
              </p>
              <p className="text-gray-500">已解锁徽章</p>
            </div>
          </div>

          <div className="flex flex-wrap gap-3">
            {rarityOrder.map((rarity) => {
              const colors = BADGE_RARITY_COLORS[rarity]
              const count = getRarityCount(rarity)
              const unlocked = getRarityUnlockedCount(rarity)
              return (
                <div
                  key={rarity}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg"
                  style={{ backgroundColor: colors.bg.includes('gradient') ? '#9B59B620' : colors.bg + '20' }}
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ background: colors.bg }}
                  />
                  <span className="text-sm font-medium text-gray-700">
                    {rarityLabels[rarity]} {unlocked}/{count}
                  </span>
                </div>
              )
            })}
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedCategory('all')}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
              selectedCategory === 'all'
                ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <Award size={16} />
            全部
          </button>
          {categoryOrder.map((category) => {
            const Icon = categoryIcons[category]
            const categoryBadges = badges.filter((b) => b.category === category)
            const categoryUnlocked = userBadges.filter((ub) => {
              const badge = badges.find((b) => b.id === ub.badgeId)
              return badge?.category === category
            }).length

            return (
              <button
                key={category}
                onClick={() => setSelectedCategory(category)}
                className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all ${
                  selectedCategory === category
                    ? 'bg-gradient-to-r from-blue-500 to-purple-500 text-white shadow-md'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                }`}
              >
                <Icon size={16} />
                {BADGE_CATEGORY_NAMES[category]}
                <span className="text-xs opacity-75">
                  {categoryUnlocked}/{categoryBadges.length}
                </span>
              </button>
            )
          })}
        </div>

        <div className="flex gap-2 mt-4">
          <Filter size={16} className="text-gray-400" />
          {(['all', 'unlocked', 'locked'] as const).map((filter) => (
            <button
              key={filter}
              onClick={() => setFilterUnlocked(filter)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                filterUnlocked === filter
                  ? 'bg-gray-800 text-white'
                  : 'text-gray-500 hover:bg-gray-100'
              }`}
            >
              {filter === 'all' ? '全部' : filter === 'unlocked' ? '已获得' : '未获得'}
            </button>
          ))}
        </div>
      </div>

      {categoryOrder.map((category) => {
        const categoryBadges = badgesByCategory[category]
        if (categoryBadges.length === 0) return null

        const CategoryIcon = categoryIcons[category]
        return (
          <div key={category} className="mb-8">
            <div className="flex items-center gap-2 mb-4">
              <CategoryIcon size={20} className="text-gray-500" />
              <h2 className="text-xl font-bold text-gray-800">
                {BADGE_CATEGORY_NAMES[category]}
              </h2>
              <span className="text-sm text-gray-400">
                {categoryBadges.filter((b) => userBadges.some((ub) => ub.badgeId === b.id)).length}/{categoryBadges.length}
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {categoryBadges.map((badge) => (
                <BadgeCard key={badge.id} badge={badge} />
              ))}
            </div>
          </div>
        )
      })}

      {filteredBadges.length === 0 && (
        <div className="text-center py-16">
          <Trophy size={48} className="mx-auto text-gray-300 mb-4" />
          <p className="text-gray-500">没有符合条件的徽章</p>
        </div>
      )}
    </div>
  )
}
