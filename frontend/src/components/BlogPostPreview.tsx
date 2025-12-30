'use client'

import { useState } from 'react'
import { ExternalLink, Eye, Code, Copy, Check, Trash2 } from 'lucide-react'
import { cn, formatDate, getStatusColor, getCategoryColor, truncate, stripHtml } from '@/lib/utils'

interface BlogPost {
  id: string
  title: string
  html_content: string
  image_url: string | null
  category: string
  status: string
  article_url: string
  created_at: string
}

interface BlogPostPreviewProps {
  post: BlogPost
  onStatusChange?: (postId: string, status: string) => void
  onDelete?: (postId: string) => void
  className?: string
}

export function BlogPostPreview({ post, onStatusChange, onDelete, className }: BlogPostPreviewProps) {
  const [viewMode, setViewMode] = useState<'preview' | 'code'>('preview')
  const [copied, setCopied] = useState(false)

  const handleCopyHtml = async () => {
    await navigator.clipboard.writeText(post.html_content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={cn(
      'rounded-2xl bg-white dark:bg-midnight-800/50 border border-midnight-200 dark:border-midnight-700 overflow-hidden',
      className
    )}>
      {/* Header */}
      <div className="p-4 border-b border-midnight-200 dark:border-midnight-700">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            <span className={cn(
              'inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium',
              getCategoryColor(post.category)
            )}>
              {post.category}
            </span>
            <span className={cn(
              'inline-flex items-center px-2.5 py-1 rounded-lg text-xs font-medium',
              getStatusColor(post.status)
            )}>
              {post.status}
            </span>
          </div>
          
          <span className="text-xs text-midnight-500 dark:text-midnight-400">
            {formatDate(post.created_at)}
          </span>
        </div>
        
        <h3 className="text-lg font-semibold text-midnight-900 dark:text-white line-clamp-2">
          {post.title}
        </h3>
        
        <p className="mt-1 text-sm text-midnight-500 dark:text-midnight-400 line-clamp-2">
          {truncate(stripHtml(post.html_content), 150)}
        </p>
      </div>

      {/* View Toggle */}
      <div className="flex items-center justify-between px-4 py-2 bg-midnight-50 dark:bg-midnight-900/50 border-b border-midnight-200 dark:border-midnight-700">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setViewMode('preview')}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
              viewMode === 'preview' 
                ? 'bg-white dark:bg-midnight-700 text-midnight-900 dark:text-white shadow-sm'
                : 'text-midnight-500 dark:text-midnight-400 hover:text-midnight-700 dark:hover:text-midnight-200'
            )}
          >
            <Eye className="w-3 h-3" />
            Preview
          </button>
          <button
            onClick={() => setViewMode('code')}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
              viewMode === 'code' 
                ? 'bg-white dark:bg-midnight-700 text-midnight-900 dark:text-white shadow-sm'
                : 'text-midnight-500 dark:text-midnight-400 hover:text-midnight-700 dark:hover:text-midnight-200'
            )}
          >
            <Code className="w-3 h-3" />
            HTML
          </button>
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyHtml}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-midnight-500 dark:text-midnight-400 hover:text-midnight-700 dark:hover:text-midnight-200 hover:bg-midnight-100 dark:hover:bg-midnight-800 transition-all"
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? 'Copied!' : 'Copy HTML'}
          </button>
          
          {post.article_url && (
            <a
              href={post.article_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-youdle-600 dark:text-youdle-400 hover:text-youdle-700 dark:hover:text-youdle-300 hover:bg-youdle-50 dark:hover:bg-youdle-900/20 transition-all"
            >
              <ExternalLink className="w-3 h-3" />
              Source
            </a>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="p-4 max-h-96 overflow-y-auto">
        {viewMode === 'preview' ? (
          <div 
            className="prose prose-sm dark:prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: post.html_content }}
          />
        ) : (
          <pre className="text-xs font-mono text-midnight-700 dark:text-midnight-300 whitespace-pre-wrap break-words bg-midnight-50 dark:bg-midnight-900 rounded-lg p-4">
            {post.html_content}
          </pre>
        )}
      </div>

      {/* Actions */}
      {onStatusChange && (
        <div className="flex items-center justify-between gap-2 p-4 border-t border-midnight-200 dark:border-midnight-700 bg-midnight-50 dark:bg-midnight-900/50">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onStatusChange(post.id, 'draft')}
              disabled={post.status === 'draft'}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                post.status === 'draft'
                  ? 'bg-midnight-200 dark:bg-midnight-700 text-midnight-500 cursor-not-allowed'
                  : 'bg-midnight-100 dark:bg-midnight-800 text-midnight-700 dark:text-midnight-300 hover:bg-midnight-200 dark:hover:bg-midnight-700'
              )}
            >
              Draft
            </button>
            <button
              onClick={() => onStatusChange(post.id, 'reviewed')}
              disabled={post.status === 'reviewed'}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                post.status === 'reviewed'
                  ? 'bg-purple-200 dark:bg-purple-900/50 text-purple-500 cursor-not-allowed'
                  : 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 hover:bg-purple-200 dark:hover:bg-purple-900/50'
              )}
            >
              Mark Reviewed
            </button>
            <button
              onClick={() => onStatusChange(post.id, 'published')}
              disabled={post.status === 'published'}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                post.status === 'published'
                  ? 'bg-green-200 dark:bg-green-900/50 text-green-500 cursor-not-allowed'
                  : 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 hover:bg-green-200 dark:hover:bg-green-900/50'
              )}
            >
              Publish
            </button>
          </div>
          {onDelete && (
            <button
              onClick={() => onDelete(post.id)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/50"
            >
              <Trash2 className="w-3 h-3" />
              Delete
            </button>
          )}
        </div>
      )}
    </div>
  )
}



