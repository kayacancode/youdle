'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Check, Loader2, Calendar, AlertCircle } from 'lucide-react'
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
  const [creationMethod, setCreationMethod] = useState<'manual' | 'queue' | null>(null)

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
      setCreationMethod(null)
    },
    onError: () => {
      setCreationMethod(null)
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
      setCreationMethod(null)
    },
    onError: () => {
      setCreationMethod(null)
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
      setCreationMethod(null)
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

  const handleCreateNewsletter = () => {
    if (selectedPostIds.length === 0 || creationMethod !== null) return
    
    setCreationMethod('manual')
    createMutation.mutate({
      title: title || undefined,
      subject: subject || undefined,
      post_ids: selectedPostIds,
    })
  }

  const handleQueueArticles = () => {
    if (creationMethod !== null) return
    
    if (!window.confirm('This will automatically queue all available articles and schedule the newsletter for Thursday 9 AM CST. Continue?')) {
      return
    }
    
    setCreationMethod('queue')
    queueArticlesMutation.mutate()
  }

  const isAnyOperationPending = createMutation.isPending || queueArticlesMutation.isPending

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Create Newsletter">
      <div className="p-6 space-y-6">
        {/* Warning about duplicate creation */}
        {isAnyOperationPending && (
          <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 mt-0.5 flex-shrink-0" />
            <div className="text-sm text-amber-800">
              <p className="font-medium">Newsletter Creation in Progress</p>
              <p className="mt-1">Please wait for the current operation to complete before creating another newsletter.</p>
            </div>
          </div>
        )}

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
            disabled={isAnyOperationPending}
            className={cn(
              "w-full px-4 py-2 rounded-lg border border-stone-300 focus:ring-2 focus:ring-youdle-500 focus:border-youdle-500 outline-none transition-all",
              isAnyOperationPending && "bg-stone-100 cursor-not-allowed"
            )}
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
            disabled={isAnyOperationPending}
            className={cn(
              "w-full px-4 py-2 rounded-lg border border-stone-300 focus:ring-2 focus:ring-youdle-500 focus:border-youdle-500 outline-none transition-all",
              isAnyOperationPending && "bg-stone-100 cursor-not-allowed"
            )}
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
                disabled={isAnyOperationPending}
                className={cn(
                  "text-xs hover:text-youdle-700 transition-colors",
                  isAnyOperationPending 
                    ? "text-stone-400 cursor-not-allowed" 
                    : "text-youdle-600"
                )}
              >
                Select All
              </button>
              <span className="text-stone-300">|</span>
              <button
                type="button"
                onClick={deselectAll}
                disabled={isAnyOperationPending}
                className={cn(
                  "text-xs hover:text-stone-700 transition-colors",
                  isAnyOperationPending 
                    ? "text-stone-400 cursor-not-allowed" 
                    : "text-stone-500"
                )}
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
                  onClick={() => !isAnyOperationPending && togglePost(post.id)}
                  disabled={isAnyOperationPending}
                  className={cn(
                    'w-full text-left p-3 rounded-lg border transition-all',
                    selectedPostIds.includes(post.id)
                      ? 'bg-youdle-50 border-youdle-300'
                      : 'bg-white border-stone-200 hover:border-stone-300',
                    isAnyOperationPending && 'cursor-not-allowed opacity-60'
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
            <p className="font-medium">
              {((createMutation.error as Error)?.message || (queueArticlesMutation.error as Error)?.message || '').includes('already queued recently') 
                ? 'Newsletter Already Queued'
                : 'Error Creating Newsletter'}
            </p>
            <p className="mt-1">
              {(createMutation.error as Error)?.message ||
               (queueArticlesMutation.error as Error)?.message ||
               'Failed to create newsletter'}
            </p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center justify-between pt-4 border-t border-stone-200">
          <button
            type="button"
            onClick={handleQueueArticles}
            disabled={isAnyOperationPending}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
              isAnyOperationPending
                ? "bg-stone-200 text-stone-500 cursor-not-allowed"
                : "bg-blue-100 text-blue-700 hover:bg-blue-200"
            )}
          >
            {queueArticlesMutation.isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Queuing...
              </>
            ) : (
              <>
                <Calendar className="w-4 h-4" />
                Queue All Articles
              </>
            )}
          </button>
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={onClose}
              disabled={isAnyOperationPending}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-all",
                isAnyOperationPending
                  ? "text-stone-500 cursor-not-allowed"
                  : "text-stone-700 hover:bg-stone-100"
              )}
            >
              {isAnyOperationPending ? 'Creating...' : 'Cancel'}
            </button>
            <button
              type="button"
              onClick={handleCreateNewsletter}
              disabled={selectedPostIds.length === 0 || isAnyOperationPending}
              className={cn(
                'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
                selectedPostIds.length === 0 || isAnyOperationPending
                  ? 'bg-stone-200 text-stone-500 cursor-not-allowed'
                  : 'bg-youdle-600 text-white hover:bg-youdle-700'
              )}
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Creating...
                </>
              ) : (
                'Create Newsletter'
              )}
            </button>
          </div>
        </div>
      </div>
    </Modal>
  )
}