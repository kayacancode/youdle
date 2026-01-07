'use client'

import { useState } from 'react'
import {
  Mail,
  Clock,
  Send,
  Eye,
  Trash2,
  Calendar,
  CheckCircle2,
  XCircle,
  X,
  Loader2,
  BarChart3
} from 'lucide-react'
import { cn, formatDate, getStatusColor } from '@/lib/utils'
import type { Newsletter } from '@/lib/api'

interface NewsletterCardProps {
  newsletter: Newsletter
  onPreview: () => void
  onSchedule: () => void
  onSend: () => void
  onUnschedule: () => void
  onDelete: () => void
  isScheduling?: boolean
  isSending?: boolean
}

export function NewsletterCard({
  newsletter,
  onPreview,
  onSchedule,
  onSend,
  onUnschedule,
  onDelete,
  isScheduling,
  isSending,
}: NewsletterCardProps) {
  const [isConfirmingDelete, setIsConfirmingDelete] = useState(false)

  const statusConfig = {
    draft: { icon: Mail, color: 'text-stone-600', bgColor: 'bg-stone-100' },
    scheduled: { icon: Clock, color: 'text-blue-600', bgColor: 'bg-blue-100' },
    sent: { icon: CheckCircle2, color: 'text-green-600', bgColor: 'bg-green-100' },
    failed: { icon: XCircle, color: 'text-red-600', bgColor: 'bg-red-100' },
  }

  const config = statusConfig[newsletter.status] || statusConfig.draft
  const StatusIcon = config.icon

  return (
    <div className="rounded-2xl bg-white border border-stone-200 overflow-hidden hover:shadow-lg transition-shadow">
      {/* Header */}
      <div className="p-4 border-b border-stone-200">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <div className={cn('p-2 rounded-lg', config.bgColor)}>
              <StatusIcon className={cn('w-4 h-4', config.color)} />
            </div>
            <span className={cn(
              'px-2.5 py-1 rounded-lg text-xs font-medium',
              getStatusColor(newsletter.status)
            )}>
              {newsletter.status}
            </span>
          </div>
          <span className="text-xs text-stone-500">
            {formatDate(newsletter.created_at)}
          </span>
        </div>

        <h3 className="text-lg font-semibold text-stone-900 line-clamp-1">
          {newsletter.title}
        </h3>
        <p className="text-sm text-stone-500 line-clamp-1 mt-1">
          Subject: {newsletter.subject}
        </p>
      </div>

      {/* Posts Preview */}
      <div className="p-4 bg-stone-50">
        <p className="text-xs font-medium text-stone-500 mb-2">
          Included Posts ({newsletter.posts.length})
        </p>
        <div className="space-y-1 max-h-24 overflow-y-auto">
          {newsletter.posts.slice(0, 3).map((post) => (
            <div key={post.id} className="text-sm text-stone-700 line-clamp-1">
              {post.title}
            </div>
          ))}
          {newsletter.posts.length > 3 && (
            <p className="text-xs text-stone-500">
              +{newsletter.posts.length - 3} more posts
            </p>
          )}
          {newsletter.posts.length === 0 && (
            <p className="text-sm text-stone-400 italic">No posts included</p>
          )}
        </div>
      </div>

      {/* Stats (for sent newsletters) */}
      {newsletter.status === 'sent' && (
        <div className="p-4 border-t border-stone-200 bg-green-50">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4 text-stone-500" />
            </div>
            <div>
              <p className="text-xs text-stone-500">Emails Sent</p>
              <p className="text-lg font-semibold text-stone-900">
                {newsletter.emails_sent}
              </p>
            </div>
            {newsletter.open_rate !== null && (
              <div>
                <p className="text-xs text-stone-500">Open Rate</p>
                <p className="text-lg font-semibold text-green-600">
                  {(newsletter.open_rate * 100).toFixed(1)}%
                </p>
              </div>
            )}
            {newsletter.click_rate !== null && (
              <div>
                <p className="text-xs text-stone-500">Click Rate</p>
                <p className="text-lg font-semibold text-blue-600">
                  {(newsletter.click_rate * 100).toFixed(1)}%
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Scheduled info */}
      {newsletter.status === 'scheduled' && newsletter.scheduled_for && (
        <div className="p-4 border-t border-stone-200 bg-blue-50">
          <div className="flex items-center gap-2 text-sm text-blue-700">
            <Calendar className="w-4 h-4" />
            <span>Scheduled for {formatDate(newsletter.scheduled_for)}</span>
          </div>
        </div>
      )}

      {/* Error info */}
      {newsletter.status === 'failed' && newsletter.error && (
        <div className="p-4 border-t border-stone-200 bg-red-50">
          <div className="flex items-center gap-2 text-sm text-red-700">
            <XCircle className="w-4 h-4" />
            <span className="line-clamp-2">{newsletter.error}</span>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between p-4 border-t border-stone-200">
        <div className="flex items-center gap-2">
          <button
            onClick={onPreview}
            className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-stone-100 text-stone-700 hover:bg-stone-200 transition-all"
          >
            <Eye className="w-3 h-3" />
            Preview
          </button>

          {newsletter.status === 'draft' && (
            <>
              <button
                onClick={onSchedule}
                disabled={isScheduling}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-100 text-blue-700 hover:bg-blue-200 transition-all disabled:opacity-50"
              >
                {isScheduling ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Clock className="w-3 h-3" />
                )}
                Schedule
              </button>
              <button
                onClick={onSend}
                disabled={isSending}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-green-100 text-green-700 hover:bg-green-200 transition-all disabled:opacity-50"
              >
                {isSending ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <Send className="w-3 h-3" />
                )}
                Send Now
              </button>
            </>
          )}

          {newsletter.status === 'scheduled' && (
            <button
              onClick={onUnschedule}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium bg-amber-100 text-amber-700 hover:bg-amber-200 transition-all"
            >
              <X className="w-3 h-3" />
              Unschedule
            </button>
          )}
        </div>

        {(newsletter.status === 'draft' || newsletter.status === 'failed') && (
          <button
            onClick={() => {
              if (isConfirmingDelete) {
                onDelete()
                setIsConfirmingDelete(false)
              } else {
                setIsConfirmingDelete(true)
                setTimeout(() => setIsConfirmingDelete(false), 3000)
              }
            }}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
              isConfirmingDelete
                ? 'bg-red-600 text-white'
                : 'bg-red-100 text-red-700 hover:bg-red-200'
            )}
          >
            <Trash2 className="w-3 h-3" />
            {isConfirmingDelete ? 'Confirm' : 'Delete'}
          </button>
        )}
      </div>
    </div>
  )
}
