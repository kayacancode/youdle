'use client'

import { useState } from 'react'
import { Star, Send, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ReviewFormProps {
  postId: string
  postTitle: string
  onSubmit: (rating: number, comment: string, feedbackType: string) => Promise<void>
  onSkip: () => void
  className?: string
}

const feedbackTypes = [
  { id: 'general', label: 'General' },
  { id: 'content', label: 'Content Quality' },
  { id: 'formatting', label: 'Formatting' },
  { id: 'accuracy', label: 'Accuracy' },
  { id: 'tone', label: 'Tone/Voice' },
]

export function ReviewForm({ postId, postTitle, onSubmit, onSkip, className }: ReviewFormProps) {
  const [rating, setRating] = useState(0)
  const [hoverRating, setHoverRating] = useState(0)
  const [comment, setComment] = useState('')
  const [feedbackType, setFeedbackType] = useState('general')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async () => {
    if (rating === 0) return
    
    setIsSubmitting(true)
    try {
      await onSubmit(rating, comment, feedbackType)
      // Reset form
      setRating(0)
      setComment('')
      setFeedbackType('general')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className={cn(
      'rounded-2xl bg-white dark:bg-midnight-800/50 border border-midnight-200 dark:border-midnight-700 p-6',
      className
    )}>
      <h3 className="text-lg font-semibold text-midnight-900 dark:text-white mb-1">
        Review Post
      </h3>
      <p className="text-sm text-midnight-500 dark:text-midnight-400 mb-6 line-clamp-1">
        {postTitle}
      </p>

      {/* Star Rating */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-midnight-700 dark:text-midnight-300 mb-3">
          Quality Rating
        </label>
        <div className="flex items-center gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <button
              key={star}
              type="button"
              onClick={() => setRating(star)}
              onMouseEnter={() => setHoverRating(star)}
              onMouseLeave={() => setHoverRating(0)}
              className="p-1 rounded-lg hover:bg-midnight-100 dark:hover:bg-midnight-800 transition-colors"
            >
              <Star
                className={cn(
                  'w-8 h-8 transition-colors',
                  (hoverRating || rating) >= star
                    ? 'fill-yellow-400 text-yellow-400'
                    : 'text-midnight-300 dark:text-midnight-600'
                )}
              />
            </button>
          ))}
          <span className="ml-2 text-sm text-midnight-500 dark:text-midnight-400">
            {rating > 0 ? `${rating}/5` : 'Select rating'}
          </span>
        </div>
      </div>

      {/* Feedback Type */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-midnight-700 dark:text-midnight-300 mb-3">
          Feedback Category
        </label>
        <div className="flex flex-wrap gap-2">
          {feedbackTypes.map((type) => (
            <button
              key={type.id}
              type="button"
              onClick={() => setFeedbackType(type.id)}
              className={cn(
                'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                feedbackType === type.id
                  ? 'bg-youdle-100 dark:bg-youdle-900/30 text-youdle-700 dark:text-youdle-300'
                  : 'bg-midnight-100 dark:bg-midnight-800 text-midnight-600 dark:text-midnight-400 hover:bg-midnight-200 dark:hover:bg-midnight-700'
              )}
            >
              {type.label}
            </button>
          ))}
        </div>
      </div>

      {/* Comment */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-midnight-700 dark:text-midnight-300 mb-2">
          Comment (Optional)
        </label>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          placeholder="What could be improved? Any specific issues?"
          rows={3}
          className="w-full px-3 py-2 rounded-lg border border-midnight-300 dark:border-midnight-600 bg-white dark:bg-midnight-900 text-midnight-900 dark:text-white placeholder-midnight-400 focus:ring-2 focus:ring-youdle-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={onSkip}
          className="px-4 py-2 rounded-lg text-sm font-medium text-midnight-600 dark:text-midnight-400 hover:text-midnight-800 dark:hover:text-midnight-200 hover:bg-midnight-100 dark:hover:bg-midnight-800 transition-all"
        >
          Skip
        </button>
        
        <button
          type="button"
          onClick={handleSubmit}
          disabled={rating === 0 || isSubmitting}
          className={cn(
            'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all',
            'bg-gradient-to-r from-youdle-500 to-youdle-600 text-white',
            'hover:from-youdle-600 hover:to-youdle-700 hover:shadow-lg hover:shadow-youdle-500/25',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {isSubmitting ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <Send className="w-4 h-4" />
          )}
          Submit Review
        </button>
      </div>
    </div>
  )
}



