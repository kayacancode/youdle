'use client'

import { useState, useEffect } from 'react'
import { Save, X, AlertCircle, Globe } from 'lucide-react'
import { Modal } from './Modal'
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
  blogger_post_id?: string | null
  blogger_url?: string | null
}

interface EditBlogPostModalProps {
  isOpen: boolean
  post: BlogPost
  onClose: () => void
  onSave: (postId: string, updates: BlogPostUpdate) => Promise<void>
}

export function EditBlogPostModal({ isOpen, post, onClose, onSave }: EditBlogPostModalProps) {
  const [formData, setFormData] = useState<BlogPostUpdate>({
    html_content: post.html_content,
    image_url: post.image_url || '',
    category: post.category as 'SHOPPERS' | 'RECALL',
  })
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Reset form when modal opens with new post data
  useEffect(() => {
    if (isOpen) {
      setFormData({
        html_content: post.html_content,
        image_url: post.image_url || '',
        category: post.category as 'SHOPPERS' | 'RECALL',
      })
      setError(null)
    }
  }, [isOpen, post])

  const handleSave = async () => {
    // Validate
    if (!formData.html_content?.trim()) {
      setError('HTML content is required')
      return
    }

    if (!formData.category) {
      setError('Category is required')
      return
    }

    setIsSaving(true)
    setError(null)

    try {
      await onSave(post.id, formData)
      onClose()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save changes')
    } finally {
      setIsSaving(false)
    }
  }

  const handleCancel = () => {
    if (!isSaving) {
      onClose()
    }
  }

  const isPublishedToBlogger = !!post.blogger_post_id

  const footerContent = (
    <div className="flex items-center justify-between">
      {/* Blogger sync indicator */}
      {isPublishedToBlogger ? (
        <div className="flex items-center gap-1.5 text-xs text-blue-600">
          <Globe className="w-3.5 h-3.5" />
          <span>Changes will sync to Blogger</span>
        </div>
      ) : (
        <div />
      )}

      <div className="flex items-center gap-2">
        <button
          onClick={handleCancel}
          disabled={isSaving}
          className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-stone-100 text-stone-700 hover:bg-stone-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <X className="w-4 h-4" />
          Cancel
        </button>
        <button
          onClick={handleSave}
          disabled={isSaving || !formData.html_content?.trim()}
          className="flex items-center gap-1 px-4 py-2 rounded-lg text-sm font-medium transition-all bg-youdle-500 text-white hover:bg-youdle-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-4 h-4" />
          {isSaving ? 'Saving...' : 'Save Changes'}
        </button>
      </div>
    </div>
  )

  return (
    <Modal isOpen={isOpen} onClose={handleCancel} title={`Edit: ${post.title}`} footer={footerContent}>
      <div className="p-6 space-y-4">
        {/* Error Message */}
        {error && (
          <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
            <AlertCircle className="w-4 h-4 mt-0.5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Category Field */}
        <div>
          <label htmlFor="category" className="block text-xs font-medium text-stone-700 mb-1">
            Category
          </label>
          <select
            id="category"
            value={formData.category}
            onChange={(e) => setFormData({ ...formData, category: e.target.value as 'SHOPPERS' | 'RECALL' })}
            disabled={isSaving}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <option value="SHOPPERS">SHOPPERS</option>
            <option value="RECALL">RECALL</option>
          </select>
        </div>

        {/* Image URL Field */}
        <div>
          <label htmlFor="image_url" className="block text-xs font-medium text-stone-700 mb-1">
            Image URL (optional)
          </label>
          <input
            id="image_url"
            type="url"
            value={formData.image_url || ''}
            onChange={(e) => setFormData({ ...formData, image_url: e.target.value })}
            placeholder="https://example.com/image.jpg"
            disabled={isSaving}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-sm focus:ring-2 focus:ring-accent-500 focus:border-transparent disabled:opacity-50 disabled:cursor-not-allowed"
          />
        </div>

        {/* HTML Content Field */}
        <div>
          <label htmlFor="html_content" className="block text-xs font-medium text-stone-700 mb-1">
            HTML Content
          </label>
          <textarea
            id="html_content"
            value={formData.html_content}
            onChange={(e) => setFormData({ ...formData, html_content: e.target.value })}
            rows={12}
            disabled={isSaving}
            className="w-full px-3 py-2 rounded-lg border border-stone-300 text-xs font-mono focus:ring-2 focus:ring-accent-500 focus:border-transparent resize-none disabled:opacity-50 disabled:cursor-not-allowed"
            placeholder="Enter HTML content..."
          />
          <p className="mt-1 text-xs text-stone-500">
            {formData.html_content?.length || 0} characters
          </p>
        </div>
      </div>
    </Modal>
  )
}
