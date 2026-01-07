'use client'

import { useQuery } from '@tanstack/react-query'
import { Loader2, ExternalLink } from 'lucide-react'
import { Modal } from './Modal'
import { api, Newsletter } from '@/lib/api'

interface NewsletterPreviewModalProps {
  isOpen: boolean
  newsletter: Newsletter
  onClose: () => void
}

export function NewsletterPreviewModal({
  isOpen,
  newsletter,
  onClose
}: NewsletterPreviewModalProps) {
  // Fetch fresh HTML preview
  const { data: preview, isLoading } = useQuery({
    queryKey: ['newsletterPreview', newsletter.id],
    queryFn: () => api.previewNewsletter(newsletter.id),
    enabled: isOpen,
  })

  const openInNewTab = () => {
    const html = preview?.html || newsletter.html_content
    const newWindow = window.open()
    if (newWindow) {
      newWindow.document.write(html)
      newWindow.document.close()
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`Preview: ${newsletter.title}`}>
      <div className="p-6">
        {/* Subject line */}
        <div className="mb-4 p-3 bg-stone-50 rounded-lg">
          <p className="text-xs font-medium text-stone-500 mb-1">Email Subject</p>
          <p className="text-sm text-stone-900">{newsletter.subject}</p>
        </div>

        {/* HTML Preview */}
        {isLoading ? (
          <div className="flex items-center justify-center py-16">
            <Loader2 className="w-8 h-8 text-youdle-500 animate-spin" />
          </div>
        ) : (
          <div className="border border-stone-200 rounded-lg overflow-hidden">
            <div className="bg-stone-100 px-4 py-2 border-b border-stone-200 flex items-center justify-between">
              <span className="text-xs font-medium text-stone-600">Email Preview</span>
              <button
                onClick={openInNewTab}
                className="flex items-center gap-1 text-xs text-youdle-600 hover:text-youdle-700 transition-colors"
              >
                <ExternalLink className="w-3 h-3" />
                Open in new tab
              </button>
            </div>
            <iframe
              srcDoc={preview?.html || newsletter.html_content}
              className="w-full h-[500px] bg-white"
              title="Newsletter Preview"
              sandbox="allow-same-origin"
            />
          </div>
        )}

        {/* Post list */}
        {newsletter.posts.length > 0 && (
          <div className="mt-4 p-3 bg-stone-50 rounded-lg">
            <p className="text-xs font-medium text-stone-500 mb-2">
              Included Posts ({newsletter.posts.length})
            </p>
            <ul className="space-y-1">
              {newsletter.posts.map((post, index) => (
                <li key={post.id} className="text-sm text-stone-700">
                  {index + 1}. {post.title}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Modal>
  )
}
