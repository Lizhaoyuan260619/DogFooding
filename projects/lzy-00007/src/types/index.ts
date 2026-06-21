export interface Habit {
  id: string
  name: string
  icon: string
  color: string
  category: string
  frequencyType: 'daily' | 'weekly' | 'monthly'
  frequencyCount: number
  reminderDays: number[]
  reminderTime: string
  reminderEnabled: boolean
  createdAt: string
  updatedAt: string
}

export type CheckInType = 'normal' | 'makeup'

export interface CheckIn {
  id: string
  habitId: string
  date: string
  type: CheckInType
  remark?: string
  checkInTime?: string
  location?: string
  makeupAt?: string
  createdAt: string
}

export interface CheckInData {
  remark?: string
  checkInTime?: string
  location?: string
}

export interface Category {
  id: string
  name: string
  icon: string
  color: string
}

export interface HabitFormData {
  name: string
  icon: string
  color: string
  category: string
  frequencyType: 'daily' | 'weekly' | 'monthly'
  frequencyCount: number
  reminderDays: number[]
  reminderTime: string
  reminderEnabled: boolean
}

export interface FormErrors {
  name?: string
  category?: string
  frequencyCount?: string
  reminderTime?: string
}

export type BadgeCategory = 'streak' | 'milestone' | 'social' | 'explorer' | 'special'
export type BadgeRarity = 'bronze' | 'silver' | 'gold' | 'platinum' | 'legendary'

export interface Badge {
  id: string
  name: string
  description: string
  icon: string
  color: string
  category: BadgeCategory
  rarity: BadgeRarity
  condition: {
    type: 'streak' | 'total_checkins' | 'habit_count' | 'category_master' | 'posts' | 'likes' | 'friends'
    target: number
    habitId?: string
    categoryId?: string
  }
  createdAt: string
}

export interface UserBadge {
  badgeId: string
  unlockedAt: string
  progress: number
}

export interface UserProfile {
  id: string
  name: string
  avatar: string
  bio: string
  level: number
  exp: number
  expToNextLevel: number
  createdAt: string
}

export interface Friend {
  id: string
  userId: string
  name: string
  avatar: string
  status: 'pending' | 'accepted' | 'blocked'
  createdAt: string
}

export interface Post {
  id: string
  userId: string
  userName: string
  userAvatar: string
  habitId?: string
  habitName?: string
  habitColor?: string
  content: string
  images: string[]
  likes: number
  likedBy: string[]
  commentCount: number
  isCheckInPost: boolean
  checkInDate?: string
  createdAt: string
  updatedAt: string
}

export interface Comment {
  id: string
  postId: string
  userId: string
  userName: string
  userAvatar: string
  content: string
  likes: number
  createdAt: string
}

export interface NewPostData {
  content: string
  habitId?: string
  images?: string[]
  isCheckInPost?: boolean
  checkInDate?: string
}

export interface CircleStats {
  totalPosts: number
  totalLikes: number
  totalComments: number
  activeUsers: number
  weeklyCheckIns: number
  monthlyCheckIns: number
}
