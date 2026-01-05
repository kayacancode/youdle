'use client'

import { ExternalLink } from 'lucide-react'
import { cn, formatDate, truncate, getCategoryColor } from '@/lib/utils'
import type { SearchResult } from '@/lib/api'

interface ArticleCardProps {
  article: SearchResult
  className?: string
}

export function ArticleCard({ article, className }: ArticleCardProps) {
  return (
    <div className={cn(
      'group relative rounded-xl bg-white  border border-stone-200  p-5 transition-all hover:shadow-lg hover:border-youdle-500/30',
      className
    )}>
      {/* Category & Score Badge */}
      <div className="flex items-center justify-between mb-3">
        <span className={cn(
          'inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium',
          getCategoryColor(article.category)
        )}>
          {article.category}
          {article.subcategory && (
            <span className="ml-1 opacity-75">• {article.subcategory}</span>
          )}
        </span>
        
        <div className="flex items-center gap-2">
          <span className="text-xs text-stone-500 ">
            Score:
          </span>
          <span className={cn(
            'inline-flex items-center px-2 py-0.5 rounded-md text-xs font-bold',
            article.score >= 200 ? 'bg-green-100 text-green-800 dark:bg-green-900/30' :
            article.score >= 150 ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400' :
            article.score >= 100 ? 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400' :
            'bg-midnight-100 text-midnight-800  '
          )}>
            {article.score.toFixed(1)}
          </span>
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



