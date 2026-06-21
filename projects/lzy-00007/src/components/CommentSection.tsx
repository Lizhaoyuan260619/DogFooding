import React, { useState } from 'react'
import { Send, Heart, Trash2 } from 'lucide-react'
import { useAppStore } from '@/store/useAppStore'
import { formatDistanceToNow } from 'date-fns'
import { zhCN } from 'date-fns/locale'

interface CommentSectionProps {
  postId: string
}

export default function CommentSection({ postId }: CommentSectionProps) {
  const { comments, userProfile, addComment, deleteComment } = useAppStore()
  const [newComment, setNewComment] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const postComments = comments.filter((c) => c.postId === postId)

  const handleSubmit = () => {
    if (!newComment.trim()) return
    setIsSubmitting(true)
    setTimeout(() => {
      addComment(postId, newComment.trim())
      setNewComment('')
      setIsSubmitting(false)
    }, 200)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit()
    }
  }

  const handleDelete = (commentId: string) => {
    if (window.confirm('确定要删除这条评论吗？')) {
      deleteComment(commentId)
    }
  }

  return (
    <div className="bg-gray-50 border-t border-gray-100">
      <div className="p-4 space-y-4">
        {postComments.length === 0 ? (
          <p className="text-center text-sm text-gray-400 py-4">暂无评论，快来抢沙发吧~</p>
        ) : (
          postComments.map((comment) => {
            const timeAgo = formatDistanceToNow(new Date(comment.createdAt), {
              addSuffix: true,
              locale: zhCN,
            })
            const isOwner = comment.userId === userProfile.id

            return (
              <div key={comment.id} className="flex gap-3 animate-fade-in">
                <img
                  src={comment.userAvatar}
                  alt={comment.userName}
                  className="w-8 h-8 rounded-full object-cover flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-800">
                        {comment.userName}
                      </span>
                      <span className="text-xs text-gray-400">{timeAgo}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <button className="p-1 hover:bg-gray-100 rounded transition-colors">
                        <Heart size={14} className="text-gray-400" />
                      </button>
                      {isOwner && (
                        <button
                          onClick={() => handleDelete(comment.id)}
                          className="p-1 hover:bg-red-50 rounded transition-colors"
                        >
                          <Trash2 size={14} className="text-gray-400 hover:text-red-500" />
                        </button>
                      )}
                    </div>
                  </div>
                  <p className="text-sm text-gray-600 mt-0.5 break-words">
                    {comment.content}
                  </p>
                </div>
              </div>
            )
          })
        )}
      </div>

      <div className="px-4 py-3 border-t border-gray-100 bg-white">
        <div className="flex gap-2">
          <img
            src={userProfile.avatar}
            alt={userProfile.name}
            className="w-8 h-8 rounded-full object-cover flex-shrink-0"
          />
          <div className="flex-1 flex gap-2">
            <input
              type="text"
              value={newComment}
              onChange={(e) => setNewComment(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="写下你的评论..."
              className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition-all"
              maxLength={200}
            />
            <button
              onClick={handleSubmit}
              disabled={!newComment.trim() || isSubmitting}
              className="px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-500 text-white rounded-lg text-sm font-medium transition-all hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-1"
            >
              <Send size={14} />
              {isSubmitting ? '发送中' : '发送'}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
