import { useState, useEffect } from 'react'
import { X, MapPin, Clock, FileText, RefreshCw } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { getToday, formatDate, getMonthlyMakeupCount } from '@/utils/date'
import { MAX_REMARK_LENGTH, MAX_LOCATION_LENGTH, MAX_MAKEUP_PER_MONTH, MAX_MAKEUP_DAYS } from '@/utils/constants'
import type { Habit, CheckInData } from '@/types'
import type { LucideIcon } from 'lucide-react'
import {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
} from 'lucide-react'

const iconMap: Record<string, LucideIcon> = {
  Dumbbell, BookOpen, Droplets, Moon, Apple, Brain, Heart,
  FootprintsIcon, Music, Pencil, Flame, Sun, Coffee, Bike,
  Palette, Code, Leaf, Zap, Star, Trophy, Target, Smile,
  Clock, TrendingUp, Pilcrow, Ear, Eye, Hand, Shield, Wind,
}

interface CheckInModalProps {
  habit: Habit
  date?: string
  onClose: () => void
}

export default function CheckInModal({ habit, date, onClose }: CheckInModalProps) {
  const { checkIns, checkIn, uncheckIn, makeupCheckIn, canMakeup } = useAppStore()
  const targetDate = date || getToday()
  const isToday = targetDate === getToday()
  const [remark, setRemark] = useState('')
  const [checkInTime, setCheckInTime] = useState('')
  const [location, setLocation] = useState('')
  const [error, setError] = useState('')

  const existingCheckIn = checkIns.find(
    (c) => c.habitId === habit.id && c.date === targetDate
  )
  const isChecked = !!existingCheckIn
  const makeupResult = canMakeup(habit.id, targetDate)
  const monthlyMakeupCount = getMonthlyMakeupCount(checkIns)
  const IconComponent = iconMap[habit.icon] || Star

  useEffect(() => {
    if (existingCheckIn) {
      setRemark(existingCheckIn.remark || '')
      setCheckInTime(existingCheckIn.checkInTime || '')
      setLocation(existingCheckIn.location || '')
    } else if (isToday) {
      const now = new Date()
      const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`
      setCheckInTime(timeStr)
    }
  }, [existingCheckIn, isToday])

  const handleCheckIn = () => {
    setError('')

    if (remark.length > MAX_REMARK_LENGTH) {
      setError(`备注不能超过${MAX_REMARK_LENGTH}字`)
      return
    }
    if (location.length > MAX_LOCATION_LENGTH) {
      setError(`地点不能超过${MAX_LOCATION_LENGTH}字`)
      return
    }
    if (checkInTime && !/^([01]?\d|2[0-3]):[0-5]\d$/.test(checkInTime)) {
      setError('请输入正确的时间格式')
      return
    }

    const data: CheckInData = {
      remark: remark.trim() || undefined,
      checkInTime: checkInTime || undefined,
      location: location.trim() || undefined,
    }

    if (isToday) {
      checkIn(habit.id, targetDate, data)
    } else {
      const result = makeupCheckIn(habit.id, targetDate, data)
      if (!result.success) {
        setError(result.reason || '补卡失败')
        return
      }
    }
    onClose()
  }

  const handleUncheckIn = () => {
    uncheckIn(habit.id, targetDate)
    onClose()
  }

  const formattedDate = (() => {
    const d = new Date(targetDate + 'T00:00:00')
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    return `${d.getMonth() + 1}月${d.getDate()}日 ${weekdays[d.getDay()]}`
  })()

  const canMakeupToday = !isToday && makeupResult.canMakeup

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4">
      <div className="w-full max-w-md rounded-2xl bg-white shadow-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between border-b border-stone-100 px-6 py-4">
          <div className="flex items-center gap-3">
            <div
              className="w-10 h-10 rounded-full flex items-center justify-center"
              style={{ backgroundColor: habit.color + '20', color: habit.color }}
            >
              <IconComponent size={20} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-stone-800">{habit.name}</h2>
              <p className="text-xs text-stone-500">{formattedDate}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="关闭"
            className="rounded-lg p-1.5 text-stone-400 transition-colors hover:bg-stone-100 hover:text-stone-600"
          >
            <X size={20} />
          </button>
        </div>

        <div className="p-6 space-y-5">
          {isChecked && existingCheckIn && (
            <div
              className="p-4 rounded-xl"
              style={{ backgroundColor: habit.color + '15' }}
            >
              <div className="flex items-center gap-2 mb-2">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center"
                  style={{ backgroundColor: habit.color, color: 'white' }}
                >
                  <svg className="w-4 h-4" viewBox="0 0 16 16" fill="none">
                    <path d="M3 8.5L6.5 12L13 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </div>
                <span className="font-medium text-stone-800">
                  {existingCheckIn.type === 'makeup' ? '已补卡' : '已打卡'}
                </span>
                {existingCheckIn.type === 'makeup' && (
                  <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 flex items-center gap-1">
                    <RefreshCw size={10} />
                    补卡
                  </span>
                )}
              </div>
              {existingCheckIn.type === 'makeup' && existingCheckIn.makeupAt && (
                <p className="text-xs text-stone-500 ml-8">
                  补卡时间：{formatDate(new Date(existingCheckIn.makeupAt), 'M月d日 HH:mm')}
                </p>
              )}
            </div>
          )}

          {!isToday && !isChecked && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-100">
              <div className="flex items-center gap-2 mb-2">
                <RefreshCw size={18} className="text-amber-600" />
                <span className="font-medium text-amber-800">补卡</span>
              </div>
              <p className="text-xs text-amber-600 mb-2">
                {makeupResult.canMakeup
                  ? `本月已补卡 ${monthlyMakeupCount}/${MAX_MAKEUP_PER_MONTH} 次`
                  : makeupResult.reason}
              </p>
              <p className="text-xs text-amber-500">
                仅可补打最近 {MAX_MAKEUP_DAYS} 天内的打卡
              </p>
            </div>
          )}

          <div>
            <label htmlFor="checkin-remark" className="flex items-center gap-2 text-sm font-medium text-stone-700 mb-2">
              <FileText size={16} className="text-stone-400" />
              打卡备注
            </label>
            <div className="relative">
              <textarea
                id="checkin-remark"
                value={remark}
                onChange={(e) => setRemark(e.target.value.slice(0, MAX_REMARK_LENGTH))}
                placeholder="记录一下今天的感受..."
                className="w-full px-4 py-3 border border-stone-200 rounded-xl text-sm text-stone-700 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent resize-none"
                rows={3}
                maxLength={MAX_REMARK_LENGTH}
                disabled={isChecked}
              />
              <span className={`absolute bottom-2 right-3 text-xs ${remark.length >= MAX_REMARK_LENGTH ? 'text-red-500' : 'text-stone-400'}`}>
                {remark.length}/{MAX_REMARK_LENGTH}
              </span>
            </div>
          </div>

          <div>
            <label htmlFor="checkin-time" className="flex items-center gap-2 text-sm font-medium text-stone-700 mb-2">
              <Clock size={16} className="text-stone-400" />
              打卡时间
            </label>
            <input
              id="checkin-time"
              type="time"
              value={checkInTime}
              onChange={(e) => setCheckInTime(e.target.value)}
              className="w-full px-4 py-3 border border-stone-200 rounded-xl text-sm text-stone-700 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent"
              disabled={isChecked}
            />
          </div>

          <div>
            <label htmlFor="checkin-location" className="flex items-center gap-2 text-sm font-medium text-stone-700 mb-2">
              <MapPin size={16} className="text-stone-400" />
              打卡地点
            </label>
            <div className="relative">
              <input
                id="checkin-location"
                type="text"
                value={location}
                onChange={(e) => setLocation(e.target.value.slice(0, MAX_LOCATION_LENGTH))}
                placeholder="如：家、办公室、健身房..."
                className="w-full px-4 py-3 border border-stone-200 rounded-xl text-sm text-stone-700 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent pr-16"
                maxLength={MAX_LOCATION_LENGTH}
                disabled={isChecked}
              />
              <span className={`absolute top-1/2 -translate-y-1/2 right-3 text-xs ${location.length >= MAX_LOCATION_LENGTH ? 'text-red-500' : 'text-stone-400'}`}>
                {location.length}/{MAX_LOCATION_LENGTH}
              </span>
            </div>
          </div>

          {error && (
            <div className="p-3 bg-red-50 border border-red-100 rounded-xl">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}
        </div>

        <div className="border-t border-stone-100 px-6 py-4 flex gap-3">
          {isChecked ? (
            <>
              <button
                onClick={onClose}
                className="flex-1 py-3 rounded-xl text-sm font-medium text-stone-600 bg-stone-100 hover:bg-stone-200 transition-colors"
              >
                关闭
              </button>
              <button
                onClick={handleUncheckIn}
                className="flex-1 py-3 rounded-xl text-sm font-medium text-white bg-red-500 hover:bg-red-600 transition-colors"
              >
                取消打卡
              </button>
            </>
          ) : (
            <>
              <button
                onClick={onClose}
                className="flex-1 py-3 rounded-xl text-sm font-medium text-stone-600 bg-stone-100 hover:bg-stone-200 transition-colors"
              >
                取消
              </button>
              <button
                onClick={handleCheckIn}
                disabled={!isToday && !canMakeupToday}
                className={`flex-1 py-3 rounded-xl text-sm font-medium text-white transition-colors ${
                  isToday || canMakeupToday
                    ? 'bg-emerald-500 hover:bg-emerald-600'
                    : 'bg-stone-300 cursor-not-allowed'
                }`}
                style={{
                  backgroundColor: isToday || canMakeupToday ? habit.color : undefined,
                }}
              >
                {isToday ? '确认打卡' : canMakeupToday ? '确认补卡' : '无法补卡'}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
