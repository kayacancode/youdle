'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { CheckSquare, RefreshCw, ChevronLeft, ChevronRight, Check, X } from 'lucide-react'
import { api } from '@/lib/api'
import { addFeedback } from '@/lib/supabase'
import { BlogPostPreview } from '@/components/BlogPostPreview'
import { ReviewForm } from '@/components/ReviewForm'
import { cn } from '@/lib/utils'

export default function ReviewPage() {
  const queryClient = useQueryClient()
  const [currentIndex, setCurrentIndex] = useState(0)

  // Fetch draft posts for review
  const { data: posts, isLoading, error } = useQuery({
    queryKey: ['reviewPosts'],
    queryFn: () => api.getPosts({ status: 'draft', limit: 50 }),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ postId, status }: { postId: string; status: string }) =>
      api.updatePostStatus(postId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['reviewPosts'] })
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const currentPost = posts?.[currentIndex]

  const handleApprove = () => {
    if (currentPost) {
      updateStatusMutation.mutate({ postId: currentPost.id, status: 'reviewed' })
      goToNext()
    }
  }

  const handleReject = () => {
    // For now, just move to next - could add a reject flow
    goToNext()
  }

  const [feedbackSubmitted, setFeedbackSubmitted] = useState(false)

  const handleSubmitReview = async (rating: number, comment: string, feedbackType: string) => {
    if (currentPost) {
      try {
        await addFeedback(currentPost.id, rating, comment)
        // Don't auto-approve or advance — let user approve/reject separately (Issue #858)
        setFeedbackSubmitted(true)
      } catch (error) {
        console.error('Failed to submit feedback:', error)
      }
    }
  }

  const handleSkip = () => {
    goToNext()
  }

  const goToNext = () => {
    if (posts && currentIndex < posts.length - 1) {
      setCurrentIndex(currentIndex + 1)
      setFeedbackSubmitted(false)
    }
  }

  const goToPrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1)
      setFeedbackSubmitted(false)
    }
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-stone-900">
            Review Queue
          </h1>
          <p className="mt-2 text-stone-500">
            Review generated posts, provide feedback, and approve for publishing.
          </p>
        </div>
        
        {posts && posts.length > 0 && (
          <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-white border border-stone-200">
            <span className="text-sm text-stone-500">
              Post
            </span>
            <span className="text-lg font-bold text-stone-900">
              {currentIndex + 1}
            </span>
            <span className="text-sm text-stone-500">
              of {posts.length}
            </span>
          </div>
        )}
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <RefreshCw className="w-8 h-8 text-youdle-500 animate-spin" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-red-800 dark:text-red-200">
            Error: {error instanceof Error ? error.message : 'Failed to load posts'}
          </p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && (!posts || posts.length === 0) && (
        <div className="text-center py-16 rounded-2xl bg-white border border-stone-200">
          <CheckSquare className="w-12 h-12 text-green-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-stone-900 mb-2">
            All Caught Up!
          </h3>
          <p className="text-stone-500 max-w-md mx-auto">
            There are no draft posts waiting for review. Generate new posts or check back later.
          </p>
        </div>
      )}

      {/* Review Interface */}
      {currentPost && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Post Preview */}
          <div className="lg:col-span-2">
            <BlogPostPreview post={currentPost} />
          </div>

          {/* Review Form */}
          <div className="space-y-4">
            {feedbackSubmitted ? (
              <div className="rounded-2xl bg-green-50 border border-green-200 p-6">
                <div className="flex items-center gap-2 mb-2">
                  <Check className="w-5 h-5 text-green-600" />
                  <h3 className="text-lg font-semibold text-green-800">Feedback Submitted</h3>
                </div>
                <p className="text-sm text-green-700">
                  Now approve or reject this post using the buttons below.
                </p>
              </div>
            ) : (
              <ReviewForm
                postId={currentPost.id}
                postTitle={currentPost.title}
                onSubmit={handleSubmitReview}
                onSkip={handleSkip}
              />
            )}

            {/* Quick Actions */}
            <div className="rounded-2xl bg-white border border-stone-200 p-4">
              <h4 className="text-sm font-medium text-midnight-700 mb-3">
                {feedbackSubmitted ? 'Now Approve or Reject' : 'Quick Actions'}
              </h4>
              <div className="grid grid-cols-2 gap-3">
                <button
                  onClick={handleApprove}
                  className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-900/50 transition-all"
                >
                  <Check className="w-4 h-4" />
                  Approve
                </button>
                <button
                  onClick={handleReject}
                  className="flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/50 transition-all"
                >
                  <X className="w-4 h-4" />
                  Reject
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Navigation */}
      {posts && posts.length > 1 && (
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={goToPrevious}
            disabled={currentIndex === 0}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all',
              currentIndex === 0
                ? 'bg-midnight-100 text-stone-600 cursor-not-allowed'
                : 'bg-midnight-100 text-midnight-700 hover:bg-midnight-200 dark:hover:bg-midnight-700'
            )}
          >
            <ChevronLeft className="w-4 h-4" />
            Previous
          </button>
          
          {/* Progress dots */}
          <div className="flex items-center gap-1">
            {posts.slice(0, 10).map((_, index) => (
              <button
                key={index}
                onClick={() => setCurrentIndex(index)}
                className={cn(
                  'w-2 h-2 rounded-full transition-all',
                  index === currentIndex
                    ? 'w-6 bg-youdle-500'
                    : 'bg-midnight-300 hover:bg-midnight-400 dark:hover:bg-midnight-500'
                )}
              />
            ))}
            {posts.length > 10 && (
              <span className="text-xs text-stone-500 ml-1">
                +{posts.length - 10}
              </span>
            )}
          </div>

          <button
            onClick={goToNext}
            disabled={currentIndex === posts.length - 1}
            className={cn(
              'flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-all',
              currentIndex === posts.length - 1
                ? 'bg-midnight-100 text-stone-600 cursor-not-allowed'
                : 'bg-midnight-100 text-midnight-700 hover:bg-midnight-200 dark:hover:bg-midnight-700'
            )}
          >
            Next
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}
    </div>
  )
}



