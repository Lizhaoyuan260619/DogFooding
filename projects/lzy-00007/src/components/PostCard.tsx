import React, { useState } from 'react'
import { Heart, MessageCircle, Share2, MoreHorizontal, Trash2 } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import type { Post } from '@/types'
import CommentSection from './CommentSection'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface PostCardProps {
  post: Post
}

export default function PostCard({ post }: PostCardProps) {
  const { userProfile, likePost, unlikePost, deletePost } = useAppStore()
  const [showComments, setShowComments] = useState(false)
  const [showMenu, setShowMenu] = useState(false)
  const [isLikeAnimating, setIsLikeAnimating] = useState(false)

  const isLiked = post.likedBy.includes(userProfile.id)
  const isOwner = post.userId === userProfile.id

  const handleLike = () => {
    if (isLiked) {
      unlikePost(post.id)
    } else {
      likePost(post.id)
      setIsLikeAnimating(true)
      setTimeout(() => setIsLikeAnimating(false), 400)
    }
  }

  const handleDelete = () => {
    if (window.confirm('确定要删除这条动态吗？')) {
      deletePost(post.id)
    }
    setShowMenu(false)
  }

  const timeAgo = formatDistanceToNow(new Date(post.createdAt), {
    addSuffix: true,
    locale: zhCN,
  })

  return (
    <div className="bg-white rounded-2xl shadow-sm overflow-hidden mb-4 animate-fade-in">
      <div className="p-4">
        <div className="flex items-start justify-between mb-3">
          <div className="flex items-center gap-3">
            <img
              src={post.userAvatar}
              alt={post.userName}
              className="w-10 h-10 rounded-full object-cover"
            />
            <div>
              <div className="flex items-center gap-2">
                <p className="font-semibold text-gray-800">{post.userName}</p>
                {post.isCheckInPost && post.habitName && (
                  <span
                    className="text-xs px-2 py-0.5 rounded-full font-medium"
                    style={{
                      backgroundColor: (post.habitColor || '#3B82F6') + '20',
                      color: post.habitColor || '#3B82F6',
                    }}
                  >
                    {post.habitName}
                  </span>
                )}
              </div>
              <p className="text-xs text-gray-400">{timeAgo}</p>
            </div>
          </div>

          {isOwner && (
            <div className="relative">
              <button
                onClick={() => setShowMenu(!showMenu)}
                className="p-1.5 rounded-lg hover:bg-gray-100 transition-colors"
              >
                <MoreHorizontal size={18} className="text-gray-400" />
              </button>

              {showMenu && (
                <div className="absolute right-0 top-full mt-1 bg-white rounded-xl shadow-lg border border-gray-100 py-1 min-w-32 z-10">
                  <button
                    onClick={handleDelete}
                    className="w-full px-4 py-2 text-left text-sm text-red-500 hover:bg-red-50 flex items-center gap-2"
                  >
                    <Trash2 size={14} />
                    删除
                  </button>
                </div>
              )}
            </div>
          )}
        </div>

        <p className="text-gray-700 leading-relaxed mb-3 whitespace-pre-wrap">
          {post.content}
        </p>

        {post.images.length > 0 && (
          <div className={`grid gap-2 mb-3 ${
            post.images.length === 1 ? 'grid-cols-1' :
            post.images.length === 2 ? 'grid-cols-2' :
            post.images.length >= 3 ? 'grid-cols-3' : ''
          }`}>
            {post.images.slice(0, 9).map((img, idx) => (
              <div
                key={idx}
                className="aspect-square rounded-xl overflow-hidden bg-gray-100"
              >
                <img
                  src={img}
                  alt=""
                  className="w-full h-full object-cover"
                />
              </div>
            ))}
          </div>
        )}

        <div className="flex items-center justify-between pt-3 border-t border-gray-100">
          <div className="flex items-center gap-6">
            <button
              onClick={handleLike}
              className={`flex items-center gap-1.5 transition-all ${
                isLiked ? 'text-red-500' : 'text-gray-500 hover:text-red-500'
              } ${isLikeAnimating ? 'animate-check-in' : ''}`}
            >
              <Heart
                size={20}
                fill={isLiked ? 'currentColor' : 'none'}
                className={isLiked ? 'text-red-500' : ''}
              />
              <span className="text-sm font-medium">{post.likes}</span>
            </button>

            <button
              onClick={() => setShowComments(!showComments)}
              className="flex items-center gap-1.5 text-gray-500 hover:text-blue-500 transition-colors"
            >
              <MessageCircle size={20} />
              <span className="text-sm font-medium">{post.commentCount}</span>
            </button>

            <button className="flex items-center gap-1.5 text-gray-500 hover:text-green-500 transition-colors">
              <Share2 size={20} />
              <span className="text-sm font-medium">分享</span>
            </button>
          </div>

          {post.checkInDate && (
            <span className="text-xs text-gray-400">
              打卡日期：{post.checkInDate}
            </span>
          )}
        </div>
      </div>

      {showComments && <CommentSection postId={post.id} />}
    </div>
  )
}
