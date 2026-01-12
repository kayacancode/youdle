'use client'

import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Image as ImageIcon,
  Upload,
  Trash2,
  RefreshCw,
  Check,
  X,
  Loader2,
  Copy,
  ExternalLink
} from 'lucide-react'
import { api, MediaItem } from '@/lib/api'
import { cn, formatDate, formatNumber } from '@/lib/utils'

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function MediaLibraryPage() {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())
  const [copiedId, setCopiedId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Query for media items
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['media'],
    queryFn: () => api.listMedia({ limit: 100 }),
  })

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (mediaId: string) => api.deleteMedia(mediaId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['media'] })
    },
  })

  // File upload handler
  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    setIsUploading(true)
    setUploadError(null)

    try {
      for (const file of Array.from(files)) {
        await api.uploadMedia(file)
      }
      queryClient.invalidateQueries({ queryKey: ['media'] })
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  // Toggle selection
  const toggleSelection = (id: string) => {
    setSelectedItems(prev => {
      const next = new Set(prev)
      if (next.has(id)) {
        next.delete(id)
      } else {
        next.add(id)
      }
      return next
    })
  }

  // Delete selected items
  const handleDeleteSelected = async () => {
    if (selectedItems.size === 0) return

    const confirmed = window.confirm(`Delete ${selectedItems.size} item(s)?`)
    if (!confirmed) return

    for (const id of selectedItems) {
      await deleteMutation.mutateAsync(id)
    }
    setSelectedItems(new Set())
  }

  // Copy URL to clipboard
  const handleCopyUrl = async (url: string, id: string) => {
    await navigator.clipboard.writeText(url)
    setCopiedId(id)
    setTimeout(() => setCopiedId(null), 2000)
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-stone-900">Media Library</h1>
          <p className="text-sm text-stone-500 mt-1">
            Upload and manage images for your blog posts
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium text-stone-600 hover:text-stone-900 hover:bg-stone-100 transition-colors"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            multiple
            onChange={handleFileSelect}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-youdle-500 text-white hover:bg-youdle-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isUploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {isUploading ? 'Uploading...' : 'Upload Images'}
          </button>
        </div>
      </div>

      {/* Error message */}
      {uploadError && (
        <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-sm">
          <X className="w-4 h-4" />
          <span>{uploadError}</span>
          <button onClick={() => setUploadError(null)} className="ml-auto hover:text-red-900">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Selection actions bar */}
      {selectedItems.size > 0 && (
        <div className="flex items-center gap-4 p-3 rounded-lg bg-stone-100 border border-stone-200">
          <span className="text-sm text-stone-600">
            {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''} selected
          </span>
          <button
            onClick={handleDeleteSelected}
            disabled={deleteMutation.isPending}
            className="flex items-center gap-1 px-3 py-1.5 rounded-md text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Delete
          </button>
          <button
            onClick={() => setSelectedItems(new Set())}
            className="ml-auto text-sm text-stone-500 hover:text-stone-700"
          >
            Clear selection
          </button>
        </div>
      )}

      {/* Stats */}
      {data && (
        <div className="flex items-center gap-4 text-sm text-stone-500">
          <span>{formatNumber(data.total)} image{data.total !== 1 ? 's' : ''}</span>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="flex items-center justify-center py-20">
          <Loader2 className="w-8 h-8 text-youdle-500 animate-spin" />
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <X className="w-12 h-12 text-red-400 mb-4" />
          <h3 className="text-lg font-medium text-stone-900">Failed to load media</h3>
          <p className="text-sm text-stone-500 mt-1">
            {error instanceof Error ? error.message : 'Unknown error'}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 px-4 py-2 rounded-lg text-sm font-medium bg-stone-100 hover:bg-stone-200 transition-colors"
          >
            Try again
          </button>
        </div>
      )}

      {/* Empty state */}
      {data && data.items.length === 0 && (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <ImageIcon className="w-16 h-16 text-stone-300 mb-4" />
          <h3 className="text-lg font-medium text-stone-900">No media yet</h3>
          <p className="text-sm text-stone-500 mt-1 max-w-sm">
            Upload images to use in your blog posts. Supported formats: JPEG, PNG, GIF, WebP.
          </p>
          <button
            onClick={() => fileInputRef.current?.click()}
            className="mt-4 flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium bg-youdle-500 text-white hover:bg-youdle-600 transition-colors"
          >
            <Upload className="w-4 h-4" />
            Upload your first image
          </button>
        </div>
      )}

      {/* Image grid */}
      {data && data.items.length > 0 && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
          {data.items.map((item) => (
            <MediaCard
              key={item.id}
              item={item}
              isSelected={selectedItems.has(item.id)}
              onToggleSelect={() => toggleSelection(item.id)}
              onCopyUrl={() => handleCopyUrl(item.public_url, item.id)}
              isCopied={copiedId === item.id}
              onDelete={() => {
                if (window.confirm('Delete this image?')) {
                  deleteMutation.mutate(item.id)
                }
              }}
            />
          ))}
        </div>
      )}
    </div>
  )
}

function MediaCard({
  item,
  isSelected,
  onToggleSelect,
  onCopyUrl,
  isCopied,
  onDelete,
}: {
  item: MediaItem
  isSelected: boolean
  onToggleSelect: () => void
  onCopyUrl: () => void
  isCopied: boolean
  onDelete: () => void
}) {
  const [isHovered, setIsHovered] = useState(false)
  const [imageError, setImageError] = useState(false)

  return (
    <div
      className={cn(
        'group relative rounded-xl overflow-hidden border-2 transition-all cursor-pointer',
        isSelected
          ? 'border-youdle-500 ring-2 ring-youdle-200'
          : 'border-stone-200 hover:border-stone-300'
      )}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onClick={onToggleSelect}
    >
      {/* Image */}
      <div className="aspect-square bg-stone-100 relative">
        {imageError ? (
          <div className="absolute inset-0 flex items-center justify-center">
            <ImageIcon className="w-8 h-8 text-stone-300" />
          </div>
        ) : (
          <img
            src={item.public_url}
            alt={item.alt_text || item.original_filename}
            className="w-full h-full object-cover"
            onError={() => setImageError(true)}
          />
        )}

        {/* Selection checkbox */}
        <div
          className={cn(
            'absolute top-2 left-2 w-6 h-6 rounded-md border-2 flex items-center justify-center transition-all',
            isSelected
              ? 'bg-youdle-500 border-youdle-500'
              : 'bg-white/80 border-stone-300 opacity-0 group-hover:opacity-100'
          )}
        >
          {isSelected && <Check className="w-4 h-4 text-white" />}
        </div>

        {/* Hover actions */}
        {isHovered && !isSelected && (
          <div className="absolute inset-0 bg-black/40 flex items-center justify-center gap-2">
            <button
              onClick={(e) => {
                e.stopPropagation()
                onCopyUrl()
              }}
              className="p-2 rounded-lg bg-white/90 hover:bg-white text-stone-700 transition-colors"
              title="Copy URL"
            >
              {isCopied ? <Check className="w-4 h-4 text-green-600" /> : <Copy className="w-4 h-4" />}
            </button>
            <a
              href={item.public_url}
              target="_blank"
              rel="noopener noreferrer"
              onClick={(e) => e.stopPropagation()}
              className="p-2 rounded-lg bg-white/90 hover:bg-white text-stone-700 transition-colors"
              title="Open in new tab"
            >
              <ExternalLink className="w-4 h-4" />
            </a>
            <button
              onClick={(e) => {
                e.stopPropagation()
                onDelete()
              }}
              className="p-2 rounded-lg bg-white/90 hover:bg-white text-red-600 transition-colors"
              title="Delete"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        )}
      </div>

      {/* Info */}
      <div className="p-2 bg-white">
        <p className="text-xs font-medium text-stone-700 truncate" title={item.original_filename}>
          {item.original_filename}
        </p>
        <p className="text-xs text-stone-400">
          {formatFileSize(item.file_size)}
        </p>
      </div>
    </div>
  )
}
