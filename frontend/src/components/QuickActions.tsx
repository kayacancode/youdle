'use client'

import { useState } from 'react'
import { Play, Search, RefreshCw } from 'lucide-react'
import { cn } from '@/lib/utils'
import { api } from '@/lib/api'

interface QuickActionsProps {
  onSearchPreview?: () => void
  onStartGeneration?: (jobId: string) => void
  className?: string
}

export function QuickActions({ onSearchPreview, onStartGeneration, className }: QuickActionsProps) {
  const [isGenerating, setIsGenerating] = useState(false)
  const [isSearching, setIsSearching] = useState(false)

  const handleStartGeneration = async () => {
    setIsGenerating(true)
    try {
      const response = await api.startGeneration({
        batch_size: 6,
        search_days_back: 30,
        model: 'gpt-4',
        use_placeholder_images: false,
      })
      onStartGeneration?.(response.job_id)
    } catch (error) {
      console.error('Failed to start generation:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const handleSearchPreview = async () => {
    setIsSearching(true)
    try {
      onSearchPreview?.()
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className={cn('rounded-2xl bg-white  border border-stone-200  p-6', className)}>
      <h3 className="text-lg font-semibold text-stone-900  mb-4">Quick Actions</h3>
      
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <button
          onClick={handleStartGeneration}
          disabled={isGenerating}
          className={cn(
            'flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all',
            'bg-gradient-to-r from-youdle-500 to-youdle-600 text-stone-900',
            'hover:from-youdle-600 hover:to-youdle-700 hover:shadow-lg hover:shadow-youdle-500/25',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          {isGenerating ? (
            <RefreshCw className="w-4 h-4 animate-spin" />
          ) : (
            <Play className="w-4 h-4" />
          )}
          Start Generation
        </button>

        <button
          onClick={handleSearchPreview}
          disabled={isSearching}
          className={cn(
            'flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all',
            'bg-midnight-100  text-midnight-700 ',
            'hover:bg-midnight-200 dark:hover:bg-midnight-600',
            'disabled:opacity-50 disabled:cursor-not-allowed'
          )}
        >
          <Search className="w-4 h-4" />
          Preview Search
        </button>

        <a
          href="/review"
          className={cn(
            'flex items-center justify-center gap-2 px-4 py-3 rounded-xl font-medium text-sm transition-all',
            'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
            'hover:bg-purple-200 dark:hover:bg-purple-900/50'
          )}
        >
          Review Posts
        </a>
      </div>
    </div>
  )
}



