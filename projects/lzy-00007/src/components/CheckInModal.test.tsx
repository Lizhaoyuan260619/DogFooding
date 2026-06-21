import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import CheckInModal from '@/components/CheckInModal'
import { useAppStore } from '@/store/useAppStore'
import { getToday, formatDate } from '@/utils/date'
import type { Habit } from '@/types'
import { subDays } from 'date-fns'
import { MAX_REMARK_LENGTH, MAX_LOCATION_LENGTH } from '@/utils/constants'

const testHabit: Habit = {
  id: 'test-habit-1',
  name: '测试习惯',
  icon: 'Star',
  color: '#10B981',
  category: 'health',
  frequencyType: 'daily',
  frequencyCount: 1,
  reminderDays: [],
  reminderTime: '09:00',
  reminderEnabled: false,
  createdAt: '2024-01-01T00:00:00.000Z',
  updatedAt: '2024-01-01T00:00:00.000Z',
}

describe('CheckInModal - 集成测试', () => {
  beforeEach(() => {
    useAppStore.setState({
      habits: [testHabit],
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

  const renderModal = (date?: string) => {
    const onClose = vi.fn()
    render(
      <CheckInModal
        habit={testHabit}
        date={date}
        onClose={onClose}
      />
    )
    return { onClose }
  }

  describe('界面渲染', () => {
    it('应该渲染习惯名称和日期', () => {
      renderModal()
      expect(screen.getByText('测试习惯')).toBeInTheDocument()
    })

    it('应该显示打卡备注输入框', () => {
      renderModal()
      expect(screen.getByPlaceholderText('记录一下今天的感受...')).toBeInTheDocument()
    })

    it('应该显示打卡时间选择器', () => {
      renderModal()
      expect(screen.getByLabelText(/打卡时间/)).toBeInTheDocument()
    })

    it('应该显示打卡地点输入框', () => {
      renderModal()
      expect(screen.getByPlaceholderText('如：家、办公室、健身房...')).toBeInTheDocument()
    })

    it('应该显示字数统计', () => {
      renderModal()
      expect(screen.getByText(`0/${MAX_REMARK_LENGTH}`)).toBeInTheDocument()
    })
  })

  describe('备注输入', () => {
    it('应该允许输入备注文字', () => {
      renderModal()
      const textarea = screen.getByPlaceholderText('记录一下今天的感受...') as HTMLTextAreaElement

      fireEvent.change(textarea, { target: { value: '今天感觉很好' } })

      expect(textarea.value).toBe('今天感觉很好')
      expect(screen.getByText(`6/${MAX_REMARK_LENGTH}`)).toBeInTheDocument()
    })

    it('应该限制备注最大字数', () => {
      renderModal()
      const textarea = screen.getByPlaceholderText('记录一下今天的感受...') as HTMLTextAreaElement
      const longText = 'a'.repeat(MAX_REMARK_LENGTH + 50)

      fireEvent.change(textarea, { target: { value: longText } })

      expect(textarea.value.length).toBe(MAX_REMARK_LENGTH)
      expect(screen.getByText(`${MAX_REMARK_LENGTH}/${MAX_REMARK_LENGTH}`)).toBeInTheDocument()
    })
  })

  describe('地点输入', () => {
    it('应该允许输入地点', () => {
      renderModal()
      const input = screen.getByPlaceholderText('如：家、办公室、健身房...') as HTMLInputElement

      fireEvent.change(input, { target: { value: '家里的书房' } })

      expect(input.value).toBe('家里的书房')
    })

    it('应该限制地点最大字数', () => {
      renderModal()
      const input = screen.getByPlaceholderText('如：家、办公室、健身房...') as HTMLInputElement
      const longText = 'a'.repeat(MAX_LOCATION_LENGTH + 20)

      fireEvent.change(input, { target: { value: longText } })

      expect(input.value.length).toBe(MAX_LOCATION_LENGTH)
    })
  })

  describe('时间选择', () => {
    it('应该允许设置打卡时间', () => {
      renderModal()
      const timeInput = screen.getByLabelText(/打卡时间/) as HTMLInputElement

      fireEvent.change(timeInput, { target: { value: '08:30' } })

      expect(timeInput.value).toBe('08:30')
    })
  })

  describe('打卡功能', () => {
    it('点击确认打卡应该调用 checkIn 并关闭模态框', () => {
      const { onClose } = renderModal()

      const confirmBtn = screen.getByText('确认打卡')
      fireEvent.click(confirmBtn)

      const checkIns = useAppStore.getState().checkIns
      expect(checkIns.length).toBe(1)
      expect(checkIns[0].type).toBe('normal')
      expect(onClose).toHaveBeenCalled()
    })

    it('打卡时应该保存备注、时间和地点信息', () => {
      renderModal()

      const textarea = screen.getByPlaceholderText('记录一下今天的感受...')
      const timeInput = screen.getByLabelText(/打卡时间/)
      const locationInput = screen.getByPlaceholderText('如：家、办公室、健身房...')

      fireEvent.change(textarea, { target: { value: '今天完成得很好' } })
      fireEvent.change(timeInput, { target: { value: '07:00' } })
      fireEvent.change(locationInput, { target: { value: '家里' } })

      const confirmBtn = screen.getByText('确认打卡')
      fireEvent.click(confirmBtn)

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.remark).toBe('今天完成得很好')
      expect(checkIn.checkInTime).toBe('07:00')
      expect(checkIn.location).toBe('家里')
    })
  })

  describe('补卡功能', () => {
    const yesterday = formatDate(subDays(new Date(), 1))

    it('对于过去的日期应该显示补卡按钮', () => {
      renderModal(yesterday)
      expect(screen.getByText('确认补卡')).toBeInTheDocument()
    })

    it('应该显示补卡提示信息', () => {
      renderModal(yesterday)
      expect(screen.getByText('补卡')).toBeInTheDocument()
    })

    it('点击确认补卡应该创建补卡记录', () => {
      const { onClose } = renderModal(yesterday)

      const confirmBtn = screen.getByText('确认补卡')
      fireEvent.click(confirmBtn)

      const checkIns = useAppStore.getState().checkIns
      expect(checkIns.length).toBe(1)
      expect(checkIns[0].type).toBe('makeup')
      expect(checkIns[0].makeupAt).toBeDefined()
      expect(onClose).toHaveBeenCalled()
    })

    it('补卡时也应该保存备注、时间和地点', () => {
      renderModal(yesterday)

      const textarea = screen.getByPlaceholderText('记录一下今天的感受...')
      fireEvent.change(textarea, { target: { value: '昨天忘记打卡了' } })

      const confirmBtn = screen.getByText('确认补卡')
      fireEvent.click(confirmBtn)

      const checkIn = useAppStore.getState().checkIns[0]
      expect(checkIn.remark).toBe('昨天忘记打卡了')
      expect(checkIn.type).toBe('makeup')
    })
  })

  describe('已打卡状态', () => {
    beforeEach(() => {
      useAppStore.setState(() => ({
        checkIns: [
          {
            id: 'checkin-1',
            habitId: testHabit.id,
            date: getToday(),
            type: 'normal',
            remark: '已完成打卡',
            checkInTime: '08:00',
            location: '办公室',
            createdAt: '2024-01-01T00:00:00.000Z',
          },
        ],
      }))
    })

    it('应该显示已打卡状态', () => {
      renderModal()
      expect(screen.getByText('已打卡')).toBeInTheDocument()
    })

    it('应该显示取消打卡按钮', () => {
      renderModal()
      expect(screen.getByText('取消打卡')).toBeInTheDocument()
    })

    it('点击取消打卡应该删除打卡记录', () => {
      const { onClose } = renderModal()

      const uncheckBtn = screen.getByText('取消打卡')
      fireEvent.click(uncheckBtn)

      const checkIns = useAppStore.getState().checkIns
      expect(checkIns.length).toBe(0)
      expect(onClose).toHaveBeenCalled()
    })
  })

  describe('关闭功能', () => {
    it('点击取消按钮应该关闭模态框', () => {
      const { onClose } = renderModal()

      const cancelBtn = screen.getByText('取消')
      fireEvent.click(cancelBtn)

      expect(onClose).toHaveBeenCalled()
    })

    it('点击关闭按钮应该关闭模态框', () => {
      const { onClose } = renderModal()

      const closeBtn = screen.getByRole('button', { name: /关闭/ })
      fireEvent.click(closeBtn)

      expect(onClose).toHaveBeenCalled()
    })
  })
})
