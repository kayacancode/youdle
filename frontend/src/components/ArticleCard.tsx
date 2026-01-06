'use client'

import { useState } from 'react'
import { ExternalLink, Info } from 'lucide-react'
import { cn, formatDate, truncate, getCategoryColor } from '@/lib/utils'
import type { SearchResult } from '@/lib/api'

interface ArticleCardProps {
  article: SearchResult
  className?: string
}

export function ArticleCard({ article, className }: ArticleCardProps) {
  const [showScoreInfo, setShowScoreInfo] = useState(false)

  return (
    <div className={cn(
      'group relative rounded-xl bg-white  border border-stone-200  p-5 transition-all hover:shadow-lg hover:border-youdle-500/30',
      className
    )}>
      {/* Category & Score Badge */}
      <div className="flex items-center justify-between mb-3">
        <span className={cn(
          'inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium text-black',
          getCategoryColor(article.category)
        )}>
          {article.category}
          {article.subcategory && (
            <span className="ml-1 opacity-75">• {article.subcategory}</span>
          )}
        </span>

        <div className="flex items-center gap-2 relative">
          <span className="text-xs text-black">
            Score:
          </span>
          <button
            onClick={() => setShowScoreInfo(!showScoreInfo)}
            className="text-stone-500 hover:text-stone-700 transition-colors"
            aria-label="Score information"
          >
            <Info className="w-3.5 h-3.5" />
          </button>
          <span className={cn(
            'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold text-black',
            article.score >= 200 ? 'bg-green-100' :
            article.score >= 150 ? 'bg-blue-100' :
            article.score >= 100 ? 'bg-yellow-100' :
            'bg-midnight-100'
          )}>
            {article.score.toFixed(1)}
          </span>

          {/* Score Info Tooltip */}
          {showScoreInfo && (
            <div className="absolute right-0 top-6 z-10 w-72 p-4 bg-white border border-stone-200 rounded-lg shadow-lg text-xs">
              <button
                onClick={() => setShowScoreInfo(false)}
                className="absolute top-2 right-2 text-stone-400 hover:text-stone-600"
              >
                ×
              </button>
              <h4 className="font-semibold text-black mb-2">Score Breakdown</h4>
              <div className="space-y-1.5 text-stone-600">
                <p><strong>Keyword Boost (×3.0):</strong> +10 pts per recall keyword (recall, salmonella, listeria, etc.)</p>
                <p><strong>First Entry Boost:</strong> +10 pts (first result) or +5 pts (others)</p>
                <p><strong>Length Score (×2.0):</strong> 200-600 chars = 80 pts (optimal)</p>
                <p><strong>Age Score (×1.0):</strong> 0-100 pts (newer = higher)</p>
                <p><strong>Category Boost:</strong> RECALL articles get +50 pts</p>
              </div>
              <p className="mt-2 text-stone-500 italic">Higher scores = more relevant articles</p>
            </div>
          )}
        </div>
      </div>

      {/* Title */}
      <h3 className="text-lg font-semibold text-stone-900  mb-2 line-clamp-2 group-hover:text-youdle-600 dark:group-hover:text-youdle-400 transition-colors">
        {article.title}
      </h3>

      {/* Description */}
      <p className="text-sm text-midnight-600  mb-4 line-clamp-3">
        {truncate(article.description.replace(/<[^>]*>/g, ''), 200)}
      </p>

      {/* Footer */}
      <div className="flex items-center justify-between pt-3 border-t border-midnight-100 ">
        <span className="text-xs text-stone-500 ">
          {formatDate(article.pubDate)}
        </span>
        
        <a
          href={article.link}
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-xs font-medium text-youdle-600 hover:text-youdle-700 dark:hover:text-youdle-300 transition-colors"
        >
          View Source
          <ExternalLink className="w-3 h-3" />
        </a>
      </div>
    </div>
  )
}



