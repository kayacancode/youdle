'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Check, Loader2, Calendar } from 'lucide-react'
import { Modal } from './Modal'
import { api, NewsletterCreate, BlogPostSummary } from '@/lib/api'
import { cn, getCategoryColor } from '@/lib/utils'

interface CreateNewsletterModalProps {
  isOpen: boolean
  onClose: () => void
  onSuccess: () => void
}

export function CreateNewsletterModal({ isOpen, onClose, onSuccess }: CreateNewsletterModalProps) {
  const [title, setTitle] = useState('')
  const [subject, setSubject] = useState('')
  const [selectedPostIds, setSelectedPostIds] = useState<string[]>([])

  // Fetch available posts
  const { data: posts, isLoading: postsLoading } = useQuery({
    queryKey: ['publishedPostsForNewsletter'],
    queryFn: () => api.getPublishedPostsForNewsletter(),
    enabled: isOpen,
  })

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: NewsletterCreate) => api.createNewsletter(data),
    onSuccess: () => {
      onSuccess()
      // Reset form
      setTitle('')
      setSubject('')
      setSelectedPostIds([])
    },
  })

  // Queue articles mutation (auto-create + schedule)
  const queueArticlesMutation = useMutation({
    mutationFn: () => api.queueArticles(),
    onSuccess: () => {
      onSuccess()
      setTitle('')
      setSubject('')
      setSelectedPostIds([])
    },
  })

  // Auto-generate title and subject when modal opens
  useEffect(() => {
    if (isOpen && !title) {
      const date = new Date().toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      })
      setTitle(`Weekly Newsletter - ${date}`)
      setSubject('')  // Leave empty — backend auto-generates content-driven subject from article titles
    }
  }, [isOpen, title])

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setTitle('')
      setSubject('')
      setSelectedPostIds([])
    }
  }, [isOpen])

  const togglePost = (postId: string) => {
    setSelectedPostIds(prev =>
      prev.includes(postId)
        ? prev.filter(id => id !== postId)
        : [...prev, postId]
    )
  }

  const selectAll = () => {
    if (posts) {
      setSelectedPostIds(posts.map(p => p.id))
    }
  }

  const deselectAll = () => {
    setSelectedPostIds([])
  }

  const handleSubmit = () => {
    if (selectedPostIds.length === 0) return

    createMutation.mutate({
      title: title || undefined,
      subject: subject || undefined,
      post_ids: selectedPostIds,
    })
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Newsletter">
      <div className="p-6 space-y-6">
        {/* Title */}
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-2">
            Title (Internal)
          </label>
          <input
            type="text"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="Weekly Newsletter - January 6, 2026"
            className="w-full px-4 py-2 rounded-lg border border-stone-300 focus:ring-2 focus:ring-youdle-500 focus:border-youdle-500 outline-none transition-all"
          />
        </div>

        {/* Subject */}
        <div>
          <label className="block text-sm font-medium text-stone-700 mb-2">
            Email Subject
          </label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            placeholder="Auto-generated from article titles (or type your own)"
            className="w-full px-4 py-2 rounded-lg border border-stone-300 focus:ring-2 focus:ring-youdle-500 focus:border-youdle-500 outline-none transition-all"
          />
        </div>

        {/* Post Selection */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-stone-700">
              Select Posts ({selectedPostIds.length} selected)
            </label>
            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={selectAll}
                className="text-xs text-youdle-600 hover:text-youdle-700"
              >
                Select All
              </button>
              <span className="text-stone-300">|</span>
              <button
                type="button"
                onClick={deselectAll}
                className="text-xs text-stone-500 hover:text-stone-700"
              >
                Clear
              </button>
            </div>
          </div>

          {postsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-youdle-500 animate-spin" />
            </div>
          ) : posts && posts.length > 0 ? (
            <div className="space-y-2 max-h-64 overflow-y-auto border border-stone-200 rounded-lg p-2">
              {posts.map((post: BlogPostSummary) => (
                <button
                  key={post.id}
                  type="button"
                  onClick={() => togglePost(post.id)}
                  className={cn(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    selectedPostIds.includes(post.id)
                      ? 'bg-youdle-50 border-youdle-300'
                      : 'bg-white border-stone-200 hover:border-stone-300'
                  )}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-stone-900 line-clamp-1">
                        {post.title}
                      </p>
                      <span className={cn(
                        'inline-block mt-1 px-2 py-0.5 rounded text-xs font-medium',
                        getCategoryColor(post.category)
                      )}>
                        {post.category}
                      </span>
                    </div>
                    {selectedPostIds.includes(post.id) && (
                      <Check className="w-5 h-5 text-youdle-600 flex-shrink-0 ml-2" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 border border-stone-200 rounded-lg bg-stone-50">
              <p className="text-sm text-stone-500">
                No published posts available. Publish blog posts first.
              </p>
            </div>
          )}
        </div>

        {/* Error message */}
        {(createMutation.isError || queueArticlesMutation.isError) && (
          <div className="p-3 rounded-lg bg-red-50 border border-red-200 text-sm text-red-700">
            {(createMutation.error as Error)?.message ||
             (queueArticlesMutation.error as Error)?.message ||
             'Failed to create newsletter'}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-stone-200">
          <button
            type="button"
            onClick={() => {
              if (window.confirm('Queue all available articles and schedule for Thursday 9 AM CST?')) {
                queueArticlesMutation.mutate()
              }
            }}
            disabled={queueArticlesMutation.isPending || createMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-all disabled:opacity-50"
          >
            {queueArticlesMutation.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Calendar className="w-4 h-4" />
            )}
            Queue Articles
          </button>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-lg text-sm font-medium text-stone-700 hover:bg-stone-100 transition-all"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={selectedPostIds.length === 0 || createMutation.isPending || queueArticlesMutation.isPending}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                selectedPostIds.length === 0
                  ? 'bg-stone-200 text-stone-500 cursor-not-allowed'
                  : 'bg-youdle-600 text-white hover:bg-youdle-700'
              )}
            >
              {createMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
              Create Newsletter
            </button>
          </div>
        </div>
      </div>
    </Modal>
  )
}
