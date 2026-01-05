'use client'

import { useState } from 'react'
import { ExternalLink, Eye, Code, Copy, Check, Trash2, Edit2 } from 'lucide-react'
import { cn, formatDate, getStatusColor, getCategoryColor, truncate, stripHtml } from '@/lib/utils'
import { EditBlogPostModal } from './EditBlogPostModal'
import type { BlogPostUpdate } from '@/lib/api'

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
  onEdit?: (postId: string, updates: BlogPostUpdate) => Promise<void>
  className?: string
}

export function BlogPostPreview({ post, onStatusChange, onDelete, onEdit, className }: BlogPostPreviewProps) {
  const [viewMode, setViewMode] = useState<'preview' | 'code'>('preview')
  const [copied, setCopied] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)

  const handleCopyHtml = async () => {
    await navigator.clipboard.writeText(post.html_content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className={cn(
      'rounded-2xl bg-white border border-stone-200 overflow-hidden',
      className
    )}>
      {/* Header */}
      <div className="p-4 border-b border-stone-200">
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

          <span className="text-xs text-stone-500">
            {formatDate(post.created_at)}
          </span>
        </div>

        <h3 className="text-lg font-semibold text-stone-900 line-clamp-2">
          {post.title}
        </h3>

        <p className="mt-1 text-sm text-stone-500 line-clamp-2">
          {truncate(stripHtml(post.html_content), 150)}
        </p>
      </div>

      {/* View Toggle */}
      <div className="flex items-center justify-between px-4 py-2 bg-stone-50 border-b border-stone-200">
        <div className="flex items-center gap-1">
          <button
            onClick={() => setViewMode('preview')}
            className={cn(
              'flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
              viewMode === 'preview'
                ? 'bg-white text-stone-900 shadow-sm'
                : 'text-stone-500 hover:text-stone-700'
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
                ? 'bg-white text-stone-900 shadow-sm'
                : 'text-stone-500 hover:text-stone-700'
            )}
          >
            <Code className="w-3 h-3" />
            HTML
          </button>
          {onEdit && (
            <button
              onClick={() => setIsEditModalOpen(true)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all text-stone-500 hover:text-stone-700 hover:bg-white"
            >
              <Edit2 className="w-3 h-3" />
              Edit
            </button>
          )}
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleCopyHtml}
            className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-stone-500 hover:text-stone-700 hover:bg-stone-100 transition-all"
          >
            {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
            {copied ? 'Copied!' : 'Copy HTML'}
          </button>

          {post.article_url && (
            <a
              href={post.article_url}
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-1 px-2 py-1 rounded-md text-xs text-accent-600 hover:text-accent-700 hover:bg-accent-50 transition-all"
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
            className="prose prose-sm max-w-none"
            dangerouslySetInnerHTML={{ __html: post.html_content }}
          />
        ) : (
          <pre className="text-xs font-mono text-stone-700 whitespace-pre-wrap break-words bg-stone-50 rounded-lg p-4">
            {post.html_content}
          </pre>
        )}
      </div>

      {/* Actions */}
      {onStatusChange && (
        <div className="flex items-center justify-between gap-2 p-4 border-t border-stone-200 bg-stone-50">
          <div className="flex items-center gap-2">
            <button
              onClick={() => onStatusChange(post.id, 'draft')}
              disabled={post.status === 'draft'}
              className={cn(
                'px-3 py-1.5 rounded-lg text-xs font-medium transition-all',
                post.status === 'draft'
                  ? 'bg-stone-200 text-stone-500 cursor-not-allowed'
                  : 'bg-stone-100 text-stone-700 hover:bg-stone-200'
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
                  ? 'bg-purple-200 text-purple-500 cursor-not-allowed'
                  : 'bg-purple-100 text-purple-700 hover:bg-purple-200'
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
                  ? 'bg-green-200 text-green-500 cursor-not-allowed'
                  : 'bg-green-100 text-green-700 hover:bg-green-200'
              )}
            >
              Publish
            </button>
          </div>
          {onDelete && (
            <button
              onClick={() => onDelete(post.id)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-all bg-red-100 text-red-700 hover:bg-red-200"
            >
              <Trash2 className="w-3 h-3" />
              Delete
            </button>
          )}
        </div>
      )}

      {/* Edit Modal */}
      {onEdit && (
        <EditBlogPostModal
          isOpen={isEditModalOpen}
          post={post}
          onClose={() => setIsEditModalOpen(false)}
          onSave={onEdit}
        />
      )}
    </div>
  )
}



