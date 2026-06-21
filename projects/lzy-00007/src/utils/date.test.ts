import { describe, it, expect } from 'vitest'
import {
  isWithinMakeupRange,
  getMonthlyMakeupCount,
  canMakeupCheckIn,
  isValidCheckInTime,
  getMakeupDatesAvailable,
  getToday,
  formatDate,
} from '@/utils/date'
import type { CheckIn } from '@/types'
import { MAX_MAKEUP_DAYS, MAX_MAKEUP_PER_MONTH } from '@/utils/constants'
import { subDays, format } from 'date-fns'

describe('Date Utilities - 补卡功能', () => {
  describe('isWithinMakeupRange', () => {
    it('应该返回 true 当日期在补卡范围内（今天）', () => {
      const today = getToday()
      expect(isWithinMakeupRange(today)).toBe(true)
    })

    it('应该返回 true 当日期在补卡范围内（6天前）', () => {
      const sixDaysAgo = formatDate(subDays(new Date(), 6))
      expect(isWithinMakeupRange(sixDaysAgo)).toBe(true)
    })

    it('应该返回 false 当日期超出补卡范围（7天前）', () => {
      const sevenDaysAgo = formatDate(subDays(new Date(), 7))
      expect(isWithinMakeupRange(sevenDaysAgo)).toBe(false)
    })

    it('应该返回 false 当日期是未来的', () => {
      const tomorrow = formatDate(subDays(new Date(), -1))
      expect(isWithinMakeupRange(tomorrow)).toBe(false)
    })
  })

  describe('getMonthlyMakeupCount', () => {
    const createMockCheckIns = (): CheckIn[] => {
      const today = new Date()
      const thisMonth = format(today, 'yyyy-MM')
      const lastMonth = format(subDays(today, 35), 'yyyy-MM')

      return [
        { id: '1', habitId: 'h1', date: `${thisMonth}-01`, type: 'makeup', createdAt: '2024-01-01T00:00:00.000Z', makeupAt: '2024-01-02T00:00:00.000Z' },
        { id: '2', habitId: 'h1', date: `${thisMonth}-05`, type: 'makeup', createdAt: '2024-01-01T00:00:00.000Z', makeupAt: '2024-01-06T00:00:00.000Z' },
        { id: '3', habitId: 'h1', date: `${thisMonth}-10`, type: 'normal', createdAt: '2024-01-01T00:00:00.000Z' },
        { id: '4', habitId: 'h2', date: `${lastMonth}-15`, type: 'makeup', createdAt: '2024-01-01T00:00:00.000Z', makeupAt: '2024-01-16T00:00:00.000Z' },
      ]
    }

    it('应该正确统计本月补卡次数', () => {
      const checkIns = createMockCheckIns()
      const count = getMonthlyMakeupCount(checkIns)
      expect(count).toBe(2)
    })

    it('应该统计指定月份的补卡次数', () => {
      const checkIns = createMockCheckIns()
      const today = new Date()
      const lastMonth = format(subDays(today, 35), 'yyyy-MM')
      const count = getMonthlyMakeupCount(checkIns, lastMonth)
      expect(count).toBe(1)
    })

    it('当没有补卡记录时应该返回 0', () => {
      const checkIns: CheckIn[] = [
        { id: '1', habitId: 'h1', date: '2024-01-01', type: 'normal', createdAt: '2024-01-01T00:00:00.000Z' },
      ]
      const count = getMonthlyMakeupCount(checkIns, '2024-01')
      expect(count).toBe(0)
    })
  })

  describe('canMakeupCheckIn', () => {
    const habitId = 'test-habit'
    const yesterday = formatDate(subDays(new Date(), 1))
    const twoDaysAgo = formatDate(subDays(new Date(), 2))
    const eightDaysAgo = formatDate(subDays(new Date(), 8))

    it('应该允许补卡当日期在范围内且未打卡且未超出次数限制', () => {
      const checkIns: CheckIn[] = []
      const result = canMakeupCheckIn(habitId, yesterday, checkIns)
      expect(result.canMakeup).toBe(true)
      expect(result.reason).toBeUndefined()
    })

    it('应该拒绝补卡当日期超出补卡范围', () => {
      const checkIns: CheckIn[] = []
      const result = canMakeupCheckIn(habitId, eightDaysAgo, checkIns)
      expect(result.canMakeup).toBe(false)
      expect(result.reason).toContain('7天')
    })

    it('应该拒绝补卡当该日期已打卡', () => {
      const checkIns: CheckIn[] = [
        { id: '1', habitId, date: yesterday, type: 'normal', createdAt: '2024-01-01T00:00:00.000Z' },
      ]
      const result = canMakeupCheckIn(habitId, yesterday, checkIns)
      expect(result.canMakeup).toBe(false)
      expect(result.reason).toContain('已打卡')
    })

    it('应该拒绝补卡当本月补卡次数已达上限', () => {
      const checkIns: CheckIn[] = []
      for (let i = 0; i < MAX_MAKEUP_PER_MONTH; i++) {
        checkIns.push({
          id: `makeup-${i}`,
          habitId: `other-habit-${i}`,
          date: formatDate(subDays(new Date(), i + 1)),
          type: 'makeup',
          createdAt: '2024-01-01T00:00:00.000Z',
          makeupAt: '2024-01-02T00:00:00.000Z',
        })
      }
      const result = canMakeupCheckIn(habitId, twoDaysAgo, checkIns)
      expect(result.canMakeup).toBe(false)
      expect(result.reason).toContain('3次')
    })

    it('应该允许补卡当本月补卡次数还剩1次', () => {
      const checkIns: CheckIn[] = []
      for (let i = 0; i < MAX_MAKEUP_PER_MONTH - 1; i++) {
        checkIns.push({
          id: `makeup-${i}`,
          habitId: `other-habit-${i}`,
          date: formatDate(subDays(new Date(), i + 1)),
          type: 'makeup',
          createdAt: '2024-01-01T00:00:00.000Z',
          makeupAt: '2024-01-02T00:00:00.000Z',
        })
      }
      const result = canMakeupCheckIn(habitId, twoDaysAgo, checkIns)
      expect(result.canMakeup).toBe(true)
    })
  })

  describe('isValidCheckInTime', () => {
    it('应该返回 true 对于有效的时间格式', () => {
      expect(isValidCheckInTime('08:30', getToday())).toBe(true)
      expect(isValidCheckInTime('23:59', getToday())).toBe(true)
      expect(isValidCheckInTime('00:00', getToday())).toBe(true)
      expect(isValidCheckInTime('12:00', getToday())).toBe(true)
    })

    it('应该返回 false 对于无效的时间格式', () => {
      expect(isValidCheckInTime('25:00', getToday())).toBe(false)
      expect(isValidCheckInTime('23:60', getToday())).toBe(false)
      expect(isValidCheckInTime('abc', getToday())).toBe(false)
      expect(isValidCheckInTime('', getToday())).toBe(false)
    })
  })

  describe('getMakeupDatesAvailable', () => {
    const habitId = 'test-habit'

    it('应该返回所有可补卡的日期（当都未打卡时）', () => {
      const checkIns: CheckIn[] = []
      const dates = getMakeupDatesAvailable(habitId, checkIns)
      expect(dates.length).toBe(MAX_MAKEUP_DAYS)
    })

    it('应该只返回未打卡的日期', () => {
      const today = getToday()
      const checkIns: CheckIn[] = [
        { id: '1', habitId, date: today, type: 'normal', createdAt: '2024-01-01T00:00:00.000Z' },
      ]
      const dates = getMakeupDatesAvailable(habitId, checkIns)
      expect(dates.length).toBe(MAX_MAKEUP_DAYS - 1)
      expect(dates).not.toContain(today)
    })
  })
})
