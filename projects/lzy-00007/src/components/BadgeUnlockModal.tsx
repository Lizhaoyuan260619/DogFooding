import React, { useEffect, useState } from 'react'
import { X, Trophy, Sparkles } from 'lucide-react'
import {
  Flame, Target, Star, Award, Send, Heart, Users, Sun, Moon, CheckCircle, Crown,
  Dumbbell, BookOpen, Brain, Droplets, Pencil, Music, Coffee, Zap
} from 'lucide-react'
import type { BadgeRarity } from '@/types'
import { BADGE_RARITY_COLORS } from '@/utils/constants'
import { useAppStore } from '@/store/useAppStore'
import type { LucideIcon } from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
  Flame, Trophy, Target, Star, Award, Send, Heart, Users, Sun, Moon, CheckCircle, Crown,
  Dumbbell, BookOpen, Brain, Droplets, Pencil, Music, Coffee, Zap,
}

interface ConfettiPiece {
  id: number
  left: number
  delay: number
  color: string
  rotation: number
}

export default function BadgeUnlockModal() {
  const { newlyUnlockedBadge, clearNewBadge } = useAppStore()
  const [show, setShow] = useState(false)
  const [confetti, setConfetti] = useState<ConfettiPiece[]>([])

  useEffect(() => {
    if (newlyUnlockedBadge) {
      const colors = ['#FFD700', '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
      const pieces: ConfettiPiece[] = Array.from({ length: 30 }, (_, i) => ({
        id: i,
        left: Math.random() * 100,
        delay: Math.random() * 0.5,
        color: colors[Math.floor(Math.random() * colors.length)],
        rotation: Math.random() * 360,
      }))
      setConfetti(pieces)
      setShow(true)
    }
  }, [newlyUnlockedBadge])

  const handleClose = () => {
    setShow(false)
    setTimeout(() => {
      clearNewBadge()
    }, 300)
  }

  if (!newlyUnlockedBadge || !show) return null

  const rarityColors = BADGE_RARITY_COLORS[newlyUnlockedBadge.rarity]
  const IconComponent = iconMap[newlyUnlockedBadge.icon] || Trophy

  const rarityLabels: Record<BadgeRarity, string> = {
    bronze: '青铜',
    silver: '白银',
    gold: '黄金',
    platinum: '铂金',
    legendary: '传奇',
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        onClick={handleClose}
      />

      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {confetti.map((piece) => (
          <div
            key={piece.id}
            className="absolute w-3 h-3 animate-confetti"
            style={{
              left: `${piece.left}%`,
              top: '0',
              backgroundColor: piece.color,
              animationDelay: `${piece.delay}s`,
              transform: `rotate(${piece.rotation}deg)`,
              borderRadius: Math.random() > 0.5 ? '50%' : '0',
            }}
          />
        ))}
      </div>

      <div className="relative bg-white rounded-3xl p-8 max-w-md w-full text-center animate-badge-unlock overflow-hidden">
        <button
          onClick={handleClose}
          className="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-100 transition-colors z-10"
        >
          <X size={20} className="text-gray-400" />
        </button>

        <div className="relative mb-6">
          <div
            className="absolute inset-0 rounded-full animate-ping opacity-30"
            style={{ backgroundColor: rarityColors.bg.includes('gradient') ? '#9B59B6' : rarityColors.bg }}
          />

          <div
            className="w-32 h-32 mx-auto rounded-full flex items-center justify-center relative animate-glow-pulse"
            style={{
              background: rarityColors.bg,
              border: `4px solid ${rarityColors.border}`,
              color: rarityColors.text === '#FFFFFF' || rarityColors.text === '#FFF8DC' ? '#FFFFFF' : rarityColors.text,
            }}
          >
            <IconComponent size={64} className="animate-float" />
            <div className="absolute inset-0 rounded-full animate-shimmer pointer-events-none" />
          </div>

          <div className="absolute top-0 right-1/4 animate-sparkle" style={{ animationDelay: '0s' }}>
            <Sparkles size={24} className="text-yellow-400" />
          </div>
          <div className="absolute bottom-4 left-1/4 animate-sparkle" style={{ animationDelay: '0.3s' }}>
            <Sparkles size={20} className="text-yellow-300" />
          </div>
          <div className="absolute top-1/2 right-0 animate-sparkle" style={{ animationDelay: '0.6s' }}>
            <Sparkles size={16} className="text-yellow-400" />
          </div>
        </div>

        <div className="text-center">
          <p className="text-sm text-gray-500 mb-2">🎉 恭喜获得新成就</p>
          <h2 className="text-3xl font-bold text-gray-800 mb-2">{newlyUnlockedBadge.name}</h2>
          <span
            className="inline-block text-sm px-4 py-1 rounded-full mb-4"
            style={{
              backgroundColor: rarityColors.bg.includes('gradient') ? '#9B59B6' : rarityColors.bg + '30',
              color: rarityColors.text === '#FFFFFF' || rarityColors.text === '#FFF8DC' ? rarityColors.border : rarityColors.text,
            }}
          >
            {rarityLabels[newlyUnlockedBadge.rarity]}成就
          </span>
          <p className="text-gray-600 mb-6">{newlyUnlockedBadge.description}</p>

          <button
            onClick={handleClose}
            className="w-full py-4 rounded-2xl font-bold text-white text-lg transition-all duration-200 hover:opacity-90 hover:scale-105"
            style={{
              background: rarityColors.bg,
            }}
          >
            太棒了！
          </button>
        </div>
      </div>
    </div>
  )
}
