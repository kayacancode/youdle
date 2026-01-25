'use client'

import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api, NewsletterReadiness } from '@/lib/api'
import { CheckCircle2, AlertCircle, Clock, Mail, Info, X } from 'lucide-react'
import { cn } from '@/lib/utils'
import Link from 'next/link'

function getNextThursday9amCST(): { date: Date; formatted: string } {
  const now = new Date()
  const dayOfWeek = now.getUTCDay() // 0 = Sunday, 4 = Thursday

  // Calculate days until next Thursday
  let daysUntilThursday = (4 - dayOfWeek + 7) % 7

  // If it's Thursday, check if we've passed 15:00 UTC (9 AM CST)
  if (daysUntilThursday === 0) {
    const currentHourUTC = now.getUTCHours()
    if (currentHourUTC >= 15) {
      daysUntilThursday = 7 // Next Thursday
    }
  }

  const nextThursday = new Date(now)
  nextThursday.setUTCDate(now.getUTCDate() + daysUntilThursday)
  nextThursday.setUTCHours(15, 0, 0, 0) // 15:00 UTC = 9:00 AM CST

  // Format the date
  const formatted = nextThursday.toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'short',
    day: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZone: 'America/Chicago'
  })

  return { date: nextThursday, formatted }
}

function getTimeRemaining(targetDate: Date): string {
  const now = new Date()
  const diffMs = targetDate.getTime() - now.getTime()

  if (diffMs <= 0) return 'now'

  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)
  const remainingHours = diffHours % 24

  if (diffDays > 0) {
    return remainingHours > 0
      ? `${diffDays} day${diffDays > 1 ? 's' : ''}, ${remainingHours} hr${remainingHours > 1 ? 's' : ''}`
      : `${diffDays} day${diffDays > 1 ? 's' : ''}`
  }

  return `${diffHours} hour${diffHours !== 1 ? 's' : ''}`
}

export function NewsletterReadinessCard() {
  const [showInfo, setShowInfo] = useState(false)

  const { data: readiness, isLoading } = useQuery<NewsletterReadiness>({
    queryKey: ['newsletterReadiness'],
    queryFn: () => api.getNewsletterReadiness(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  if (isLoading) {
    return (
      <div className="w-full rounded-xl bg-stone-50 border border-stone-200 p-6 animate-pulse">
        <div className="h-6 bg-stone-200 rounded w-1/3 mb-4" />
        <div className="space-y-3">
          <div className="h-4 bg-stone-200 rounded w-full" />
          <div className="h-4 bg-stone-200 rounded w-full" />
        </div>
      </div>
    )
  }

  if (!readiness?.success) {
    return null
  }

  const isReady = readiness.meets_requirement
  const nextThursday = getNextThursday9amCST()
  const timeRemaining = getTimeRemaining(nextThursday.date)
  const totalNeeded = readiness.shoppers_needed + readiness.recall_needed

  return (
    <div
      className={cn(
        'w-full rounded-xl border p-6 transition-all',
        isReady
          ? 'bg-green-50 border-green-200'
          : 'bg-amber-50 border-amber-200'
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              'flex items-center justify-center w-10 h-10 rounded-lg',
              isReady ? 'bg-green-100' : 'bg-amber-100'
            )}
          >
            <Mail className={cn('w-5 h-5', isReady ? 'text-green-600' : 'text-amber-600')} />
          </div>
          <div className="flex items-center gap-2">
            <div>
              <h3 className="text-lg font-semibold text-stone-900">Newsletter Readiness</h3>
              <p className="text-sm text-stone-500">This week's publishing status</p>
            </div>
            <button
              onClick={() => setShowInfo(!showInfo)}
              className="p-1 rounded-full hover:bg-stone-200 transition-colors"
              aria-label="Show information"
            >
              <Info className="w-4 h-4 text-stone-400 hover:text-stone-600" />
            </button>
          </div>
        </div>
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium',
            isReady ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'
          )}
        >
          {isReady ? (
            <>
              <CheckCircle2 className="w-4 h-4" />
              Ready
            </>
          ) : (
            <>
              <AlertCircle className="w-4 h-4" />
              {totalNeeded} more needed
            </>
          )}
        </div>
      </div>

      {/* Info Panel */}
      {showInfo && (
        <div className="mb-4 p-4 bg-white rounded-lg border border-stone-200 shadow-sm">
          <div className="flex items-start justify-between mb-2">
            <h4 className="font-medium text-stone-900">How this works</h4>
            <button
              onClick={() => setShowInfo(false)}
              className="p-0.5 rounded hover:bg-stone-100 transition-colors"
            >
              <X className="w-4 h-4 text-stone-400" />
            </button>
          </div>
          <ul className="text-sm text-stone-600 space-y-2">
            <li className="flex gap-2">
              <span className="text-stone-400">•</span>
              <span>Blog posts are generated every <strong>Tuesday at 9 AM CST</strong></span>
            </li>
            <li className="flex gap-2">
              <span className="text-stone-400">•</span>
              <span>The newsletter is sent every <strong>Thursday at 9 AM CST</strong></span>
            </li>
            <li className="flex gap-2">
              <span className="text-stone-400">•</span>
              <span>Requirements: <strong>6 Shoppers</strong> + <strong>1 Recall</strong> articles must be published to Blogger</span>
            </li>
            <li className="flex gap-2">
              <span className="text-stone-400">•</span>
              <span>Only posts created this week (since Tuesday) count toward the requirement</span>
            </li>
            <li className="flex gap-2">
              <span className="text-stone-400">•</span>
              <span>If requirements aren't met by Thursday, the newsletter will be cancelled</span>
            </li>
          </ul>
        </div>
      )}

      {/* Progress bars */}
      <div className="space-y-4">
        {/* Shoppers progress */}
        <div>
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-stone-600 font-medium">Shoppers Articles</span>
            <span className="font-semibold text-stone-900">
              {readiness.shoppers_published} / {readiness.shoppers_required}
            </span>
          </div>
          <div className="h-2.5 bg-stone-200 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all duration-500',
                readiness.shoppers_published >= readiness.shoppers_required
                  ? 'bg-green-500'
                  : 'bg-amber-500'
              )}
              style={{
                width: `${Math.min(100, (readiness.shoppers_published / readiness.shoppers_required) * 100)}%`,
              }}
            />
          </div>
        </div>

        {/* Recall progress */}
        <div>
          <div className="flex justify-between text-sm mb-1.5">
            <span className="text-stone-600 font-medium">Recall Alerts</span>
            <span className="font-semibold text-stone-900">
              {readiness.recall_published} / {readiness.recall_required}
            </span>
          </div>
          <div className="h-2.5 bg-stone-200 rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full rounded-full transition-all duration-500',
                readiness.recall_published >= readiness.recall_required
                  ? 'bg-green-500'
                  : 'bg-amber-500'
              )}
              style={{
                width: `${Math.min(100, (readiness.recall_published / readiness.recall_required) * 100)}%`,
              }}
            />
          </div>
        </div>
      </div>

      {/* Footer with deadline and action */}
      <div className="mt-5 pt-4 border-t border-stone-200 flex items-center justify-between">
        <div className="flex items-center gap-2 text-sm text-stone-500">
          <Clock className="w-4 h-4" />
          <span>
            Newsletter sends in <span className="font-medium text-stone-700">{timeRemaining}</span>
          </span>
        </div>

        {!isReady && (
          <Link
            href="/posts?status=reviewed"
            className="px-4 py-2 bg-youdle-500 text-white text-sm font-medium rounded-lg hover:bg-youdle-600 transition-colors"
          >
            Publish Posts
          </Link>
        )}
      </div>
    </div>
  )
}
