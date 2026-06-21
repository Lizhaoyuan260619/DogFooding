import React, { useState } from 'react'
import { Lock, Sparkles } from 'lucide-react'
import {
  Flame, Trophy, Target, Star, Award, Send, Heart, Users, Sun, Moon, CheckCircle, Crown,
  Dumbbell, BookOpen, Brain, Droplets, Pencil, Music, Coffee, Zap
} from 'lucide-react'
import type { Badge, BadgeRarity } from '@/types'
import { BADGE_RARITY_COLORS } from '@/utils/constants'
import { useAppStore } from '@/store/useAppStore'
import type { LucideIcon } from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
  Flame, Trophy, Target, Star, Award, Send, Heart, Users, Sun, Moon, CheckCircle, Crown,
  Dumbbell, BookOpen, Brain, Droplets, Pencil, Music, Coffee, Zap,
}

interface BadgeCardProps {
  badge: Badge
  showProgress?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export default function BadgeCard({ badge, showProgress = true, size = 'md' }: BadgeCardProps) {
  const { userBadges, getBadgeProgress } = useAppStore()
  const [showDetail, setShowDetail] = useState(false)

  const isUnlocked = userBadges.some((ub) => ub.badgeId === badge.id)
  const progress = getBadgeProgress(badge)
  const userBadge = userBadges.find((ub) => ub.badgeId === badge.id)
  const rarityColors = BADGE_RARITY_COLORS[badge.rarity]

  const IconComponent = iconMap[badge.icon] || Trophy

  const sizeClasses = {
    sm: 'w-16 h-16',
    md: 'w-24 h-24',
    lg: 'w-32 h-32',
  }

  const iconSizes = {
    sm: 24,
    md: 36,
    lg: 48,
  }

  const rarityLabels: Record<BadgeRarity, string> = {
    bronze: '青铜',
    silver: '白银',
    gold: '黄金',
    platinum: '铂金',
    legendary: '传奇',
  }

  return (
    <>
      <div
        className="relative flex flex-col items-center cursor-pointer group transition-transform duration-300 hover:scale-105"
        onClick={() => setShowDetail(true)}
      >
        {isUnlocked && (
          <div className="absolute -top-1 -right-1 z-10">
            <Sparkles size={16} className="text-yellow-400 animate-sparkle" />
          </div>
        )}

        <div
          className={`${sizeClasses[size]} rounded-full flex items-center justify-center relative transition-all duration-300 ${
            isUnlocked ? 'badge-unlocked' : 'badge-locked'
          }`}
          style={{
            background: rarityColors.bg,
            border: `3px solid ${rarityColors.border}`,
            boxShadow: isUnlocked ? `0 8px 32px ${rarityColors.glow}` : 'none',
          }}
        >
          {isUnlocked ? (
            <IconComponent
              size={iconSizes[size]}
              className={size === 'lg' ? 'animate-float' : ''}
              style={{ color: rarityColors.text }}
            />
          ) : (
            <Lock size={iconSizes[size] * 0.6} className="text-gray-400" />
          )}

          {isUnlocked && size !== 'sm' && (
            <div className="absolute inset-0 rounded-full animate-shimmer pointer-events-none" />
          )}
        </div>

        {size !== 'sm' && (
          <>
            <p className={`mt-2 text-sm font-semibold text-gray-800 text-center max-w-24 truncate`}>
              {badge.name}
            </p>
            <span
              className="text-xs px-2 py-0.5 rounded-full mt-1"
              style={{
                backgroundColor: rarityColors.bg.includes('gradient') ? '#9B59B6' : rarityColors.bg + '30',
                color: rarityColors.text === '#FFFFFF' || rarityColors.text === '#FFF8DC' ? rarityColors.border : rarityColors.text,
              }}
            >
              {rarityLabels[badge.rarity]}
            </span>
          </>
        )}

        {showProgress && !isUnlocked && (
          <div className="w-full mt-2">
            <div className="h-1.5 bg-gray-200 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all duration-500 animate-progress-fill"
                style={{
                  width: `${progress}%`,
                  backgroundColor: badge.color,
                }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-1 text-center">{progress}%</p>
          </div>
        )}

        {showProgress && isUnlocked && userBadge && (
          <p className="text-xs text-emerald-500 mt-2 font-medium">
            {new Date(userBadge.unlockedAt).toLocaleDateString('zh-CN')} 解锁
          </p>
        )}
      </div>

      {showDetail && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setShowDetail(false)}
        >
          <div
            className="bg-white rounded-2xl p-6 max-w-sm w-full animate-badge-unlock"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex flex-col items-center">
              <div
                className={`${sizeClasses.lg} rounded-full flex items-center justify-center relative mb-4 ${
                  isUnlocked ? 'badge-unlocked' : 'badge-locked'
                }`}
                style={{
                  background: rarityColors.bg,
                  border: `4px solid ${rarityColors.border}`,
                  boxShadow: isUnlocked ? `0 8px 32px ${rarityColors.glow}` : 'none',
                }}
              >
                {isUnlocked ? (
                  <IconComponent size={48} style={{ color: rarityColors.text }} />
                ) : (
                  <Lock size={32} className="text-gray-400" />
                )}
                {isUnlocked && (
                    <div className="absolute inset-0 rounded-full animate-shimmer pointer-events-none" />
                )}
              </div>

              <h3 className="text-xl font-bold text-gray-800 mb-1">{badge.name}</h3>
              <span
                className="text-sm px-3 py-1 rounded-full mb-3"
                style={{
                  backgroundColor: rarityColors.bg.includes('gradient')
                    ? '#9B59B6'
                    : rarityColors.bg + '30',
                  color:
                    rarityColors.text === '#FFFFFF' || rarityColors.text === '#FFF8DC'
                      ? rarityColors.border
                      : rarityColors.text,
                }}
              >
                {rarityLabels[badge.rarity]}
              </span>

              <p className="text-gray-600 text-center mb-4">{badge.description}</p>

              {!isUnlocked && (
                <div className="w-full mb-4">
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-500">进度</span>
                    <span className="font-medium" style={{ color: badge.color }}>
                      {progress}%
                    </span>
                  </div>
                  <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500"
                      style={{
                        width: `${progress}%`,
                        backgroundColor: badge.color,
                      }}
                    />
                  </div>
                </div>
              )}

              {isUnlocked && userBadge && (
                <p className="text-sm text-emerald-500 font-medium">
                  解锁时间：{new Date(userBadge.unlockedAt).toLocaleString('zh-CN')}
                </p>
              )}

              <button
                onClick={() => setShowDetail(false)}
                className="mt-6 w-full py-3 rounded-xl font-medium text-white transition-all duration-200 hover:opacity-90"
                style={{ backgroundColor: badge.color }}
              >
                关闭
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
