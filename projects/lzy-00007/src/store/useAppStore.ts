import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import type {
  Habit,
  CheckIn,
  Category,
  Badge,
  UserBadge,
  UserProfile,
  Friend,
  Post,
  Comment,
  NewPostData,
  CircleStats,
  CheckInData,
} from '@/types'
import {
  DEFAULT_CATEGORIES,
  DEFAULT_BADGES,
  MOCK_FRIENDS,
  DEFAULT_AVATARS,
  EXP_PER_LEVEL,
  EXP_PER_CHECKIN,
  EXP_PER_POST,
} from '@/utils/constants'
import { generateId, getToday, getStreak, canMakeupCheckIn } from '@/utils/date'

interface AppStore {
  habits: Habit[]
  checkIns: CheckIn[]
  categories: Category[]
  badges: Badge[]
  userBadges: UserBadge[]
  userProfile: UserProfile
  friends: Friend[]
  posts: Post[]
  comments: Comment[]
  initialized: boolean
  newlyUnlockedBadge: Badge | null

  addHabit: (habit: Omit<Habit, 'id' | 'createdAt' | 'updatedAt'>) => void
  updateHabit: (id: string, updates: Partial<Habit>) => void
  deleteHabit: (id: string) => void

  checkIn: (habitId: string, date: string, data?: CheckInData) => void
  uncheckIn: (habitId: string, date: string) => void
  makeupCheckIn: (habitId: string, date: string, data?: CheckInData) => { success: boolean; reason?: string }
  canMakeup: (habitId: string, date: string) => { canMakeup: boolean; reason?: string }

  addCategory: (category: Omit<Category, 'id'>) => void
  deleteCategory: (id: string) => void

  checkAndUnlockBadges: () => Badge | null
  clearNewBadge: () => void

  addExp: (amount: number) => void

  createPost: (data: NewPostData) => void
  deletePost: (postId: string) => void
  likePost: (postId: string) => void
  unlikePost: (postId: string) => void

  addComment: (postId: string, content: string) => void
  deleteComment: (commentId: string) => void

  acceptFriend: (friendId: string) => void
  removeFriend: (friendId: string) => void

  getCircleStats: () => CircleStats
  getBadgeProgress: (badge: Badge) => number

  initDemoData: () => void
}

const defaultUserProfile: UserProfile = {
  id: 'user-self',
  name: '我的账号',
  avatar: DEFAULT_AVATARS[0],
  bio: '坚持每一天，遇见更好的自己',
  level: 1,
  exp: 0,
  expToNextLevel: EXP_PER_LEVEL,
  createdAt: new Date().toISOString(),
}

export const useAppStore = create<AppStore>()(
  persist(
    (set, get) => ({
      habits: [],
      checkIns: [],
      categories: DEFAULT_CATEGORIES,
      badges: DEFAULT_BADGES,
      userBadges: [],
      userProfile: defaultUserProfile,
      friends: [],
      posts: [],
      comments: [],
      initialized: false,
      newlyUnlockedBadge: null,

      addHabit: (habitData) => {
        const now = new Date().toISOString()
        const habit: Habit = {
          ...habitData,
          id: generateId(),
          createdAt: now,
          updatedAt: now,
        }
        set((state) => ({ habits: [...state.habits, habit] }))
        get().checkAndUnlockBadges()
      },

      updateHabit: (id, updates) => {
        set((state) => ({
          habits: state.habits.map((h) =>
            h.id === id ? { ...h, ...updates, updatedAt: new Date().toISOString() } : h
          ),
        }))
      },

      deleteHabit: (id) => {
        set((state) => ({
          habits: state.habits.filter((h) => h.id !== id),
          checkIns: state.checkIns.filter((c) => c.habitId !== id),
          posts: state.posts.filter((p) => p.habitId !== id),
        }))
      },

      checkIn: (habitId, date, data) => {
        const exists = get().checkIns.some(
          (c) => c.habitId === habitId && c.date === date
        )
        if (exists) return
        const checkIn: CheckIn = {
          id: generateId(),
          habitId,
          date,
          type: 'normal',
          remark: data?.remark || undefined,
          checkInTime: data?.checkInTime || undefined,
          location: data?.location || undefined,
          createdAt: new Date().toISOString(),
        }
        set((state) => ({ checkIns: [...state.checkIns, checkIn] }))
        get().addExp(EXP_PER_CHECKIN)
        get().checkAndUnlockBadges()
      },

      uncheckIn: (habitId, date) => {
        set((state) => ({
          checkIns: state.checkIns.filter(
            (c) => !(c.habitId === habitId && c.date === date)
          ),
        }))
      },

      makeupCheckIn: (habitId, date, data) => {
        const { checkIns } = get()
        const result = canMakeupCheckIn(habitId, date, checkIns)
        if (!result.canMakeup) {
          return { success: false, reason: result.reason }
        }
        const checkIn: CheckIn = {
          id: generateId(),
          habitId,
          date,
          type: 'makeup',
          remark: data?.remark || undefined,
          checkInTime: data?.checkInTime || undefined,
          location: data?.location || undefined,
          makeupAt: new Date().toISOString(),
          createdAt: new Date().toISOString(),
        }
        set((state) => ({ checkIns: [...state.checkIns, checkIn] }))
        get().addExp(EXP_PER_CHECKIN)
        get().checkAndUnlockBadges()
        return { success: true }
      },

      canMakeup: (habitId, date) => {
        return canMakeupCheckIn(habitId, date, get().checkIns)
      },

      addCategory: (categoryData) => {
        const category: Category = {
          ...categoryData,
          id: generateId(),
        }
        set((state) => ({ categories: [...state.categories, category] }))
      },

      deleteCategory: (id) => {
        set((state) => ({
          categories: state.categories.filter((c) => c.id !== id),
        }))
      },

      getBadgeProgress: (badge) => {
        const { checkIns, habits, posts, userBadges, friends, categories } = get()
        const existingUserBadge = userBadges.find((ub) => ub.badgeId === badge.id)
        if (existingUserBadge && existingUserBadge.progress >= badge.condition.target) {
          return 100
        }

        let progress = 0
        const { type, target } = badge.condition

        switch (type) {
          case 'streak': {
            const maxStreak = habits.reduce((max, h) => {
              const streak = getStreak(h.id, checkIns)
              return Math.max(max, streak)
            }, 0)
            progress = Math.min(100, (maxStreak / target) * 100)
            break
          }
          case 'total_checkins': {
            const total = checkIns.length
            progress = Math.min(100, (total / target) * 100)
            break
          }
          case 'habit_count': {
            progress = Math.min(100, (habits.length / target) * 100)
            break
          }
          case 'category_master': {
            const usedCategories = new Set<string>()
            checkIns.forEach((ci) => {
              const habit = habits.find((h) => h.id === ci.habitId)
              if (habit) usedCategories.add(habit.category)
            })
            progress = Math.min(100, (usedCategories.size / categories.length) * 100)
            break
          }
          case 'posts': {
            const userPosts = posts.filter((p) => p.userId === 'user-self')
            progress = Math.min(100, (userPosts.length / target) * 100)
            break
          }
          case 'likes': {
            const totalLikes = posts
              .filter((p) => p.userId === 'user-self')
              .reduce((sum, p) => sum + p.likes, 0)
            progress = Math.min(100, (totalLikes / target) * 100)
            break
          }
          case 'friends': {
            const acceptedFriends = friends.filter((f) => f.status === 'accepted')
            progress = Math.min(100, (acceptedFriends.length / target) * 100)
            break
          }
        }

        return Math.round(progress)
      },

      checkAndUnlockBadges: () => {
        const { badges, userBadges, getBadgeProgress } = get()
        let newlyUnlocked: Badge | null = null

        const newUserBadges = [...userBadges]

        for (const badge of badges) {
          const alreadyUnlocked = userBadges.some((ub) => ub.badgeId === badge.id)
          if (alreadyUnlocked) continue

          const progress = getBadgeProgress(badge)
          if (progress >= 100) {
            newUserBadges.push({
              badgeId: badge.id,
              unlockedAt: new Date().toISOString(),
              progress: 100,
            })
            if (!newlyUnlocked) {
              newlyUnlocked = badge
            }
          }
        }

        if (newUserBadges.length !== userBadges.length) {
          set({
            userBadges: newUserBadges,
            newlyUnlockedBadge: newlyUnlocked,
          })
        }

        return newlyUnlocked
      },

      clearNewBadge: () => {
        set({ newlyUnlockedBadge: null })
      },

      addExp: (amount) => {
        set((state) => {
          let newExp = state.userProfile.exp + amount
          let newLevel = state.userProfile.level
          let newExpToNext = state.userProfile.expToNextLevel

          while (newExp >= newExpToNext) {
            newExp -= newExpToNext
            newLevel++
            newExpToNext = Math.floor(EXP_PER_LEVEL * Math.pow(1.2, newLevel - 1))
          }

          return {
            userProfile: {
              ...state.userProfile,
              exp: newExp,
              level: newLevel,
              expToNextLevel: newExpToNext,
            },
          }
        })
      },

      createPost: (data) => {
        const { userProfile, habits } = get()
        const habit = data.habitId ? habits.find((h) => h.id === data.habitId) : undefined

        const post: Post = {
          id: generateId(),
          userId: userProfile.id,
          userName: userProfile.name,
          userAvatar: userProfile.avatar,
          habitId: data.habitId,
          habitName: habit?.name,
          habitColor: habit?.color,
          content: data.content,
          images: data.images || [],
          likes: 0,
          likedBy: [],
          commentCount: 0,
          isCheckInPost: data.isCheckInPost || false,
          checkInDate: data.checkInDate,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        }

        set((state) => ({ posts: [post, ...state.posts] }))
        get().addExp(EXP_PER_POST)
        get().checkAndUnlockBadges()
      },

      deletePost: (postId) => {
        set((state) => ({
          posts: state.posts.filter((p) => p.id !== postId),
          comments: state.comments.filter((c) => c.postId !== postId),
        }))
      },

      likePost: (postId) => {
        const { userProfile } = get()
        set((state) => ({
          posts: state.posts.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  likes: p.likes + 1,
                  likedBy: [...p.likedBy, userProfile.id],
                }
              : p
          ),
        }))
      },

      unlikePost: (postId) => {
        const { userProfile } = get()
        set((state) => ({
          posts: state.posts.map((p) =>
            p.id === postId
              ? {
                  ...p,
                  likes: Math.max(0, p.likes - 1),
                  likedBy: p.likedBy.filter((id) => id !== userProfile.id),
                }
              : p
          ),
        }))
      },

      addComment: (postId, content) => {
        const { userProfile } = get()
        const comment: Comment = {
          id: generateId(),
          postId,
          userId: userProfile.id,
          userName: userProfile.name,
          userAvatar: userProfile.avatar,
          content,
          likes: 0,
          createdAt: new Date().toISOString(),
        }

        set((state) => ({
          comments: [...state.comments, comment],
          posts: state.posts.map((p) =>
            p.id === postId ? { ...p, commentCount: p.commentCount + 1 } : p
          ),
        }))
      },

      deleteComment: (commentId) => {
        const comment = get().comments.find((c) => c.id === commentId)
        if (!comment) return

        set((state) => ({
          comments: state.comments.filter((c) => c.id !== commentId),
          posts: state.posts.map((p) =>
            p.id === comment.postId ? { ...p, commentCount: Math.max(0, p.commentCount - 1) } : p
          ),
        }))
      },

      acceptFriend: (friendId) => {
        set((state) => ({
          friends: state.friends.map((f) =>
            f.id === friendId ? { ...f, status: 'accepted' as const } : f
          ),
        }))
        get().checkAndUnlockBadges()
      },

      removeFriend: (friendId) => {
        set((state) => ({
          friends: state.friends.filter((f) => f.id !== friendId),
        }))
      },

      getCircleStats: () => {
        const { posts, comments, friends, checkIns } = get()
        const now = new Date()
        const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000)
        const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000)

        const weeklyCheckIns = checkIns.filter(
          (c) => new Date(c.date) >= weekAgo
        ).length

        const monthlyCheckIns = checkIns.filter(
          (c) => new Date(c.date) >= monthAgo
        ).length

        const totalLikes = posts.reduce((sum, p) => sum + p.likes, 0)
        const uniqueUsers = new Set(posts.map((p) => p.userId))

        return {
          totalPosts: posts.length,
          totalLikes,
          totalComments: comments.length,
          activeUsers: uniqueUsers.size + friends.filter((f) => f.status === 'accepted').length,
          weeklyCheckIns,
          monthlyCheckIns,
        }
      },

      initDemoData: () => {
        if (get().initialized) return
        const now = new Date().toISOString()
        const today = getToday()

        const demoHabits: Habit[] = [
          {
            id: 'demo-1',
            name: '晨跑30分钟',
            icon: 'Dumbbell',
            color: '#F97316',
            category: 'fitness',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [1, 2, 3, 4, 5],
            reminderTime: '07:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-2',
            name: '阅读1小时',
            icon: 'BookOpen',
            color: '#3B82F6',
            category: 'learning',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [],
            reminderTime: '21:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-3',
            name: '冥想15分钟',
            icon: 'Brain',
            color: '#8B5CF6',
            category: 'mindfulness',
            frequencyType: 'weekly',
            frequencyCount: 3,
            reminderDays: [1, 3, 5],
            reminderTime: '08:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-4',
            name: '喝8杯水',
            icon: 'Droplets',
            color: '#10B981',
            category: 'health',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [],
            reminderTime: '09:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
          {
            id: 'demo-5',
            name: '写日记',
            icon: 'Pencil',
            color: '#EC4899',
            category: 'creative',
            frequencyType: 'daily',
            frequencyCount: 1,
            reminderDays: [],
            reminderTime: '22:00',
            reminderEnabled: false,
            createdAt: now,
            updatedAt: now,
          },
        ]

        const demoCheckIns: CheckIn[] = []
        for (let i = 30; i >= 0; i--) {
          const d = new Date()
          d.setDate(d.getDate() - i)
          const dateStr = d.toISOString().split('T')[0]

          for (const habit of demoHabits) {
            const shouldCheckIn = Math.random() > (habit.frequencyType === 'weekly' ? 0.5 : 0.2)
            if (shouldCheckIn && dateStr !== today) {
              demoCheckIns.push({
                id: generateId() + i + habit.id,
                habitId: habit.id,
                date: dateStr,
                type: 'normal',
                createdAt: d.toISOString(),
              })
            }
          }
        }

        const demoFriends: Friend[] = MOCK_FRIENDS.map((f) => ({
          ...f,
          userId: f.id,
          createdAt: now,
        }))

        const demoPosts: Post[] = []
        const postContents = [
          '今天早起跑步，空气真好！🏃‍♂️',
          '读完了《原子习惯》，受益匪浅',
          '冥想第10天，感觉越来越专注了',
          '今天喝够了8杯水，加油！💪',
          '今天的日记写了很长，记录了很多想法',
          '一周运动打卡完成！感觉身体状态很好',
          '学习了新的知识，每天进步一点点',
          '坚持就是胜利！已经连续打卡15天了',
        ]

        for (let i = 10; i >= 0; i--) {
          const d = new Date()
          d.setDate(d.getDate() - i)
          const dateStr = d.toISOString().split('T')[0]
          const isToday = dateStr === today

          if (isToday && i === 0) continue

          const friend = MOCK_FRIENDS[i % MOCK_FRIENDS.length]
          const habit = demoHabits[i % demoHabits.length]
          const content = postContents[i % postContents.length]

          demoPosts.push({
            id: generateId() + i,
            userId: friend.id,
            userName: friend.name,
            userAvatar: friend.avatar,
            habitId: habit.id,
            habitName: habit.name,
            habitColor: habit.color,
            content,
            images: [],
            likes: Math.floor(Math.random() * 20),
            likedBy: [],
            commentCount: Math.floor(Math.random() * 5),
            isCheckInPost: true,
            checkInDate: dateStr,
            createdAt: d.toISOString(),
            updatedAt: d.toISOString(),
          })
        }

        const demoComments: Comment[] = []
        demoPosts.forEach((post, idx) => {
          if (post.commentCount > 0) {
            for (let i = 0; i < post.commentCount; i++) {
              const friend = MOCK_FRIENDS[(idx + i) % MOCK_FRIENDS.length]
              demoComments.push({
                id: generateId() + idx + i,
                postId: post.id,
                userId: friend.id,
                userName: friend.name,
                userAvatar: friend.avatar,
                content: ['太棒了！', '加油坚持！', '向你学习！', '真厉害！'][i % 4],
                likes: Math.floor(Math.random() * 5),
                createdAt: new Date(Date.now() - i * 3600000).toISOString(),
              })
            }
          }
        })

        const demoUserBadges: UserBadge[] = []
        const unlockedBadgeIds = ['total-10', 'habits-3', 'streak-7']
        DEFAULT_BADGES.forEach((badge) => {
          if (unlockedBadgeIds.includes(badge.id)) {
            demoUserBadges.push({
              badgeId: badge.id,
              unlockedAt: new Date(Date.now() - Math.random() * 7 * 24 * 3600000).toISOString(),
              progress: 100,
            })
          }
        })

        const totalCheckIns = demoCheckIns.length
        const expFromCheckIns = totalCheckIns * EXP_PER_CHECKIN
        const expFromPosts = 3 * EXP_PER_POST
        const totalExp = expFromCheckIns + expFromPosts
        let level = 1
        let exp = totalExp
        let expToNext = EXP_PER_LEVEL

        while (exp >= expToNext) {
          exp -= expToNext
          level++
          expToNext = Math.floor(EXP_PER_LEVEL * Math.pow(1.2, level - 1))
        }

        set({
          habits: demoHabits,
          checkIns: demoCheckIns,
          friends: demoFriends,
          posts: demoPosts,
          comments: demoComments,
          userBadges: demoUserBadges,
          userProfile: {
            ...defaultUserProfile,
            level,
            exp,
            expToNextLevel: expToNext,
          },
          initialized: true,
        })
      },
    }),
    {
      name: 'habit-tracker-storage',
    }
  )
)
