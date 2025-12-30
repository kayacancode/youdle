import { clsx, type ClassValue } from 'clsx'
import { twMerge } from 'tailwind-merge'

/**
 * Merge Tailwind CSS classes with clsx
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * Format a date string for display
 */
export function formatDate(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  }).format(date)
}

/**
 * Format relative time (e.g., "2 hours ago")
 */
export function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A'
  
  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)

  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  
  return formatDate(dateString)
}

/**
 * Truncate text to a maximum length
 */
export function truncate(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text
  return text.slice(0, maxLength - 3) + '...'
}

/**
 * Get status color classes
 */
export function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    pending: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    running: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400',
    completed: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    failed: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    cancelled: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400',
    draft: 'bg-slate-100 text-slate-800 dark:bg-slate-900/30 dark:text-slate-400',
    reviewed: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-400',
    published: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
  }
  
  return colors[status] || colors.pending
}

/**
 * Get category color classes
 */
export function getCategoryColor(category: string): string {
  const colors: Record<string, string> = {
    SHOPPERS: 'bg-youdle-100 text-youdle-800 dark:bg-youdle-900/30 dark:text-youdle-400',
    RECALL: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
  }
  
  return colors[category] || colors.SHOPPERS
}

/**
 * Parse and clean HTML content for preview
 */
export function stripHtml(html: string): string {
  return html.replace(/<[^>]*>/g, '').trim()
}

/**
 * Format a number with commas
 */
export function formatNumber(num: number): string {
  return new Intl.NumberFormat('en-US').format(num)
}

/**
 * Calculate elapsed time between two dates
 * Returns a formatted string like "2m 30s" or "1h 5m"
 */
export function formatElapsedTime(startDate: string | null | undefined, endDate?: string | null | undefined): string {
  if (!startDate) return 'N/A'

  const start = new Date(startDate)
  const end = endDate ? new Date(endDate) : new Date()
  const diffMs = end.getTime() - start.getTime()

  if (diffMs < 0) return 'N/A'

  const seconds = Math.floor(diffMs / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)

  if (hours > 0) {
    const remainingMinutes = minutes % 60
    return remainingMinutes > 0 ? `${hours}h ${remainingMinutes}m` : `${hours}h`
  }

  if (minutes > 0) {
    const remainingSeconds = seconds % 60
    return remainingSeconds > 0 ? `${minutes}m ${remainingSeconds}s` : `${minutes}m`
  }

  return `${seconds}s`
}



