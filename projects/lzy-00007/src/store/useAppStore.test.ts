import { describe, it, expect, beforeEach } from 'vitest'
import { useAppStore } from '@/store/useAppStore'
import { getToday, formatDate } from '@/utils/date'
import { MAX_MAKEUP_PER_MONTH } from '@/utils/constants'
import type { Habit } from '@/types'
import { subDays } from 'date-fns'

describe('App Store - 打卡功能增强', () => {
  beforeEach(() => {
    useAppStore.setState({
      habits: [],
      checkIns: [],
      categories: [],
      badges: [],
      userBadges: [],
      friends: [],
      posts: [],
      comments: [],
      initialized: false,
      newlyUnlockedBadge: null,
    })
  })

  const addTestHabit = (id = 'test-habit-1'): Habit => {
    const habit: Habit = {
      id,
      name: '测试习惯',
      icon: 'Star',
      color: '#10B981',
      category: 'health',
      frequencyType: 'daily',
      frequencyCount: 1,
      reminderDays: [],
      reminderTime: '09:00',
      reminderEnabled: false,
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }
    useAppStore.setState((state) => ({ habits: [...state.habits, habit] }))
    return habit
  }

  describe('checkIn - 正常打卡', () => {
    it('应该成功创建正常打卡记录', () => {
      const habit = addTestHabit()
      const today = getToday()

      useAppStore.getState().checkIn(habit.id, today)

      const checkIns = useAppStore.getState().checkIns
      expect(checkIns.length).toBe(1)
      expect(checkIns[0].habitId).toBe(habit.id)
      expect(checkIns[0].date).toBe(today)
      expect(checkIns[0].type).toBe('normal')
      expect(checkIns[0].createdAt).toBeDefined()
    })

    it('应该支持添加备注信息', () => {
      const habit = addTestHabit()
      const today = getToday()
      const remark = '今天状态很好！'

      useAppStore.getState().checkIn(habit.id, today, { remark })

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.remark).toBe(remark)
    })

    it('应该支持添加打卡时间', () => {
      const habit = addTestHabit()
      const today = getToday()
      const checkInTime = '08:30'

      useAppStore.getState().checkIn(habit.id, today, { checkInTime })

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.checkInTime).toBe(checkInTime)
    })

    it('应该支持添加打卡地点', () => {
      const habit = addTestHabit()
      const today = getToday()
      const location = '办公室'

      useAppStore.getState().checkIn(habit.id, today, { location })

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.location).toBe(location)
    })

    it('应该支持同时添加备注、时间和地点', () => {
      const habit = addTestHabit()
      const today = getToday()

      useAppStore.getState().checkIn(habit.id, today, {
        remark: '今天完成得很好',
        checkInTime: '07:00',
        location: '家里',
      })

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.remark).toBe('今天完成得很好')
      expect(checkIn.checkInTime).toBe('07:00')
      expect(checkIn.location).toBe('家里')
    })

    it('重复打卡不应该创建新记录', () => {
      const habit = addTestHabit()
      const today = getToday()

      useAppStore.getState().checkIn(habit.id, today)
      useAppStore.getState().checkIn(habit.id, today)

      const checkIns = useAppStore.getState().checkIns
      expect(checkIns.length).toBe(1)
    })
  })

  describe('makeupCheckIn - 补卡功能', () => {
    it('应该成功创建补卡记录', () => {
      const habit = addTestHabit()
      const yesterday = formatDate(subDays(new Date(), 1))

      const result = useAppStore.getState().makeupCheckIn(habit.id, yesterday)

      expect(result.success).toBe(true)
      const checkIns = useAppStore.getState().checkIns
      expect(checkIns.length).toBe(1)
      expect(checkIns[0].type).toBe('makeup')
      expect(checkIns[0].makeupAt).toBeDefined()
    })

    it('补卡记录应该支持备注、时间和地点', () => {
      const habit = addTestHabit()
      const yesterday = formatDate(subDays(new Date(), 1))

      const result = useAppStore.getState().makeupCheckIn(habit.id, yesterday, {
        remark: '昨天忘记打卡了',
        checkInTime: '21:00',
        location: '健身房',
      })

      expect(result.success).toBe(true)
      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.remark).toBe('昨天忘记打卡了')
      expect(checkIn.checkInTime).toBe('21:00')
      expect(checkIn.location).toBe('健身房')
      expect(checkIn.type).toBe('makeup')
    })

    it('当日期超出补卡范围时应该失败', () => {
      const habit = addTestHabit()
      const eightDaysAgo = formatDate(subDays(new Date(), 8))

      const result = useAppStore.getState().makeupCheckIn(habit.id, eightDaysAgo)

      expect(result.success).toBe(false)
      expect(result.reason).toContain('7天')
      expect(useAppStore.getState().checkIns.length).toBe(0)
    })

    it('当日期已打卡时应该失败', () => {
      const habit = addTestHabit()
      const yesterday = formatDate(subDays(new Date(), 1))

      useAppStore.getState().checkIn(habit.id, yesterday)
      const result = useAppStore.getState().makeupCheckIn(habit.id, yesterday)

      expect(result.success).toBe(false)
      expect(result.reason).toContain('已打卡')
    })

    it('当月补卡次数达上限时应该失败', () => {
      addTestHabit()
      addTestHabit('test-habit-2')
      addTestHabit('test-habit-3')
      addTestHabit('test-habit-4')

      for (let i = 1; i <= MAX_MAKEUP_PER_MONTH; i++) {
        const date = formatDate(subDays(new Date(), i))
        useAppStore.getState().makeupCheckIn(`test-habit-${i}`, date)
      }

      const nextDate = formatDate(subDays(new Date(), MAX_MAKEUP_PER_MONTH + 1))
      const result = useAppStore.getState().makeupCheckIn('test-habit-4', nextDate)

      expect(result.success).toBe(false)
      expect(result.reason).toContain('3次')
    })

    it('补卡应该增加经验值', () => {
      const habit = addTestHabit()
      const yesterday = formatDate(subDays(new Date(), 1))
      const initialExp = useAppStore.getState().userProfile.exp

      useAppStore.getState().makeupCheckIn(habit.id, yesterday)

      const newExp = useAppStore.getState().userProfile.exp
      expect(newExp).toBeGreaterThan(initialExp)
    })
  })

  describe('canMakeup - 补卡验证', () => {
    it('应该返回可以补卡当满足所有条件', () => {
      const habit = addTestHabit()
      const yesterday = formatDate(subDays(new Date(), 1))

      const result = useAppStore.getState().canMakeup(habit.id, yesterday)

      expect(result.canMakeup).toBe(true)
      expect(result.reason).toBeUndefined()
    })

    it('应该返回不可以补卡当日期超出范围', () => {
      const habit = addTestHabit()
      const eightDaysAgo = formatDate(subDays(new Date(), 8))

      const result = useAppStore.getState().canMakeup(habit.id, eightDaysAgo)

      expect(result.canMakeup).toBe(false)
      expect(result.reason).toBeDefined()
    })
  })

  describe('uncheckIn - 取消打卡', () => {
    it('应该能取消正常打卡', () => {
      const habit = addTestHabit()
      const today = getToday()

      useAppStore.getState().checkIn(habit.id, today)
      expect(useAppStore.getState().checkIns.length).toBe(1)

      useAppStore.getState().uncheckIn(habit.id, today)
      expect(useAppStore.getState().checkIns.length).toBe(0)
    })

    it('应该能取消补卡记录', () => {
      const habit = addTestHabit()
      const yesterday = formatDate(subDays(new Date(), 1))

      useAppStore.getState().makeupCheckIn(habit.id, yesterday)
      expect(useAppStore.getState().checkIns.length).toBe(1)

      useAppStore.getState().uncheckIn(habit.id, yesterday)
      expect(useAppStore.getState().checkIns.length).toBe(0)
    })
  })

  describe('数据完整性验证', () => {
    it('打卡记录应该包含所有必需字段', () => {
      const habit = addTestHabit()
      const today = getToday()

      useAppStore.getState().checkIn(habit.id, today, {
        remark: '测试备注',
        checkInTime: '10:00',
        location: '测试地点',
      })

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.id).toBeDefined()
      expect(checkIn.habitId).toBe(habit.id)
      expect(checkIn.date).toBe(today)
      expect(checkIn.type).toBe('normal')
      expect(checkIn.remark).toBe('测试备注')
      expect(checkIn.checkInTime).toBe('10:00')
      expect(checkIn.location).toBe('测试地点')
      expect(checkIn.createdAt).toBeDefined()
      expect(checkIn.makeupAt).toBeUndefined()
    })

    it('补卡记录应该包含 makeupAt 时间戳', () => {
      const habit = addTestHabit()
      const yesterday = formatDate(subDays(new Date(), 1))

      useAppStore.getState().makeupCheckIn(habit.id, yesterday)

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.type).toBe('makeup')
      expect(checkIn.makeupAt).toBeDefined()
      expect(typeof checkIn.makeupAt).toBe('string')
    })
  })
})
