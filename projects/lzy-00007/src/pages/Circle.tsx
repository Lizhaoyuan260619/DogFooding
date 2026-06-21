import React, { useState } from 'react'
import { Users, Clock, TrendingUp, UserPlus, Check } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import PostComposer from '@/components/PostComposer'
import PostCard from '@/components/PostCard'
import CircleStatsCard from '@/components/CircleStatsCard'

type TabType = 'trending' | 'latest' | 'following'

export default function Circle() {
  const { posts, friends, acceptFriend } = useAppStore()
  const [activeTab, setActiveTab] = useState<TabType>('latest')
  const [postCreated, setPostCreated] = useState(0)

  const pendingFriends = friends.filter((f) => f.status === 'pending')
  const acceptedFriends = friends.filter((f) => f.status === 'accepted')

  const sortedPosts = [...posts].sort((a, b) => {
    switch (activeTab) {
      case 'trending':
        return b.likes + b.commentCount * 2 - (a.likes + a.commentCount * 2)
      case 'latest':
      default:
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    }
  })

  const handlePostSuccess = () => {
    setPostCreated((prev) => prev + 1)
  }

  const tabs: { key: TabType; label: string; icon: React.ElementType }[] = [
    { key: 'latest', label: '最新', icon: Clock },
    { key: 'trending', label: '热门', icon: TrendingUp },
    { key: 'following', label: '关注', icon: Users },
  ]

  return (
    <div className="animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
            <Users className="text-blue-500" />
            打卡圈
          </h1>
          <p className="text-gray-500 mt-1">与志同道合的伙伴一起成长</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3 space-y-6">
          <PostComposer onSuccess={handlePostSuccess} key={postCreated} />

          <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
            <div className="flex border-b border-gray-100">
              {tabs.map(({ key, label, icon: Icon }) => (
                <button
                  key={key}
                  onClick={() => setActiveTab(key)}
                  className={`flex-1 flex items-center justify-center gap-2 py-4 px-4 font-medium text-sm transition-all ${
                    activeTab === key
                      ? 'text-blue-500 border-b-2 border-blue-500 bg-blue-50/50'
                      : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Icon size={16} />
                  {label}
                </button>
              ))}
            </div>
          </div>

          {sortedPosts.length > 0 ? (
            sortedPosts.map((post) => <PostCard key={post.id} post={post} />)
          ) : (
            <div className="bg-white rounded-2xl shadow-sm p-12 text-center">
              <Users size={48} className="mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 mb-2">暂无动态</p>
              <p className="text-sm text-gray-400">
                发布第一条打卡动态，与大家分享你的进步吧！
              </p>
            </div>
          )}
        </div>

        <div className="space-y-6">
          <div className="lg:sticky lg:top-8 space-y-6">
            <CircleStatsCard />

            {pendingFriends.length > 0 && (
              <div className="bg-white rounded-2xl shadow-sm p-4">
                <div className="flex items-center justify-between mb-4">
                  <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                    <UserPlus size={18} className="text-blue-500" />
                    好友请求
                    <span className="bg-red-500 text-white text-xs px-2 py-0.5 rounded-full">
                      {pendingFriends.length}
                    </span>
                  </h3>
                </div>
                <div className="space-y-3">
                  {pendingFriends.map((friend) => (
                    <div
                      key={friend.id}
                      className="flex items-center justify-between p-3 bg-gray-50 rounded-xl"
                    >
                      <div className="flex items-center gap-3">
                        <img
                          src={friend.avatar}
                          alt={friend.name}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                        <span className="font-medium text-gray-700">{friend.name}</span>
                      </div>
                      <button
                        onClick={() => acceptFriend(friend.id)}
                        className="px-3 py-1.5 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors flex items-center gap-1"
                      >
                        <Check size={14} />
                        接受
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="bg-white rounded-2xl shadow-sm p-4">
              <div className="flex items-center justify-between mb-4">
                <h3 className="font-semibold text-gray-800 flex items-center gap-2">
                  <Users size={18} className="text-green-500" />
                  我的好友
                </h3>
                <span className="text-sm text-gray-500">
                  {acceptedFriends.length} 人
                </span>
              </div>
              <div className="flex flex-wrap gap-2">
                {acceptedFriends.map((friend) => (
                  <div
                    key={friend.id}
                    className="flex flex-col items-center gap-1 p-2 rounded-xl hover:bg-gray-50 transition-colors cursor-pointer group"
                    title={friend.name}
                  >
                    <div className="relative">
                      <img
                        src={friend.avatar}
                        alt={friend.name}
                        className="w-12 h-12 rounded-full object-cover ring-2 ring-transparent group-hover:ring-green-300 transition-all"
                      />
                      <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-green-500 rounded-full border-2 border-white" />
                    </div>
                    <span className="text-xs text-gray-500 max-w-14 truncate">
                      {friend.name}
                    </span>
                  </div>
                ))}
              </div>
              {acceptedFriends.length === 0 && (
                <p className="text-center text-sm text-gray-400 py-4">
                  还没有好友，快去添加吧~
                </p>
              )}
            </div>

            <div className="bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl p-5 text-white">
              <h3 className="font-bold text-lg mb-2">💡 打卡小提示</h3>
              <p className="text-white/80 text-sm leading-relaxed">
                每天坚持打卡不仅能养成好习惯，还能解锁更多成就徽章，
                获得经验值升级，成为圈子里的打卡达人！
              </p>
              <div className="mt-4 flex items-center gap-2">
                <div className="flex -space-x-2">
                  {acceptedFriends.slice(0, 3).map((f) => (
                    <img
                      key={f.id}
                      src={f.avatar}
                      alt=""
                      className="w-8 h-8 rounded-full border-2 border-white"
                    />
                  ))}
                </div>
                <span className="text-sm text-white/70">
                  {acceptedFriends.length + 1} 人正在和你一起坚持
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
