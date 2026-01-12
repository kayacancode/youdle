'use client'

import { useState, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Check, Upload, Loader2, Image as ImageIcon, X } from 'lucide-react'
import { Modal } from './Modal'
import { api, MediaItem } from '@/lib/api'
import { cn } from '@/lib/utils'

interface MediaPickerModalProps {
  isOpen: boolean
  onClose: () => void
  onSelect: (media: MediaItem) => void
  title?: string
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export function MediaPickerModal({
  isOpen,
  onClose,
  onSelect,
  title = 'Select Image',
}: MediaPickerModalProps) {
  const queryClient = useQueryClient()
  const fileInputRef = useRef<HTMLInputElement>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [isUploading, setIsUploading] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)

  // Fetch media items
  const { data, isLoading, error } = useQuery({
    queryKey: ['media'],
    queryFn: () => api.listMedia({ limit: 100 }),
    enabled: isOpen,
  })

  // Reset state when modal closes
  const handleClose = () => {
    setSelectedId(null)
    setUploadError(null)
    onClose()
  }

  // Handle selection
  const handleSelect = () => {
    const selected = data?.items.find((m) => m.id === selectedId)
    if (selected) {
      onSelect(selected)
      handleClose()
    }
  }

  // Handle file upload
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    setUploadError(null)

    try {
      const newMedia = await api.uploadMedia(file)
      queryClient.invalidateQueries({ queryKey: ['media'] })
      setSelectedId(newMedia.id)
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setIsUploading(false)
      if (fileInputRef.current) {
        fileInputRef.current.value = ''
      }
    }
  }

  const footerContent = (
    <div className="flex items-center justify-between">
      <div className="text-xs text-stone-500">
        {data?.items.length || 0} image{data?.items.length !== 1 ? 's' : ''} available
      </div>
      <div className="flex items-center gap-2">
        <button
          onClick={handleClose}
          className="px-4 py-2 rounded-lg text-sm font-medium text-stone-700 bg-stone-100 hover:bg-stone-200 transition-colors"
        >
          Cancel
        </button>
        <button
          onClick={handleSelect}
          disabled={!selectedId}
          className="px-4 py-2 rounded-lg text-sm font-medium text-white bg-youdle-500 hover:bg-youdle-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Select Image
        </button>
      </div>
    </div>
  )

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title={title} footer={footerContent}>
      <div className="p-4 space-y-4">
        {/* Upload section */}
        <div className="flex items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept="image/jpeg,image/png,image/gif,image/webp"
            onChange={handleFileUpload}
            className="hidden"
          />
          <button
            onClick={() => fileInputRef.current?.click()}
            disabled={isUploading}
            className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium border border-stone-300 text-stone-700 hover:bg-stone-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isUploading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {isUploading ? 'Uploading...' : 'Upload New'}
          </button>
          {uploadError && (
            <span className="text-xs text-red-600">{uploadError}</span>
          )}
        </div>

        {/* Loading state */}
        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-youdle-500 animate-spin" />
          </div>
        )}

        {/* Error state */}
        {error && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-red-50 text-red-700 text-sm">
            <X className="w-4 h-4" />
            <span>{error instanceof Error ? error.message : 'Failed to load media'}</span>
          </div>
        )}

        {/* Empty state */}
        {data && data.items.length === 0 && (
          <div className="flex flex-col items-center justify-center py-12 text-center">
            <ImageIcon className="w-12 h-12 text-stone-300 mb-3" />
            <p className="text-sm text-stone-500">No images uploaded yet</p>
            <p className="text-xs text-stone-400 mt-1">Upload an image to get started</p>
          </div>
        )}

        {/* Image grid */}
        {data && data.items.length > 0 && (
          <div className="grid grid-cols-4 gap-3 max-h-[400px] overflow-y-auto pr-1">
            {data.items.map((item) => (
              <MediaPickerItem
                key={item.id}
                item={item}
                isSelected={selectedId === item.id}
                onSelect={() => setSelectedId(item.id)}
              />
            ))}
          </div>
        )}
      </div>
    </Modal>
  )
}

function MediaPickerItem({
  item,
  isSelected,
  onSelect,
}: {
  item: MediaItem
  isSelected: boolean
  onSelect: () => void
}) {
  const [imageError, setImageError] = useState(false)

  return (
    <button
      onClick={onSelect}
      className={cn(
        'relative aspect-square rounded-lg overflow-hidden border-2 transition-all focus:outline-none focus:ring-2 focus:ring-youdle-400 focus:ring-offset-2',
        isSelected
          ? 'border-youdle-500 ring-2 ring-youdle-200'
          : 'border-stone-200 hover:border-stone-300'
      )}
    >
      {imageError ? (
        <div className="absolute inset-0 flex items-center justify-center bg-stone-100">
          <ImageIcon className="w-6 h-6 text-stone-300" />
        </div>
      ) : (
        <img
          src={item.public_url}
          alt={item.alt_text || item.original_filename}
          className="w-full h-full object-cover"
          onError={() => setImageError(true)}
        />
      )}

      {/* Selection indicator */}
      {isSelected && (
        <div className="absolute inset-0 bg-youdle-500/20 flex items-center justify-center">
          <div className="w-8 h-8 rounded-full bg-youdle-500 flex items-center justify-center">
            <Check className="w-5 h-5 text-white" />
          </div>
        </div>
      )}

      {/* Filename tooltip on hover */}
      <div className="absolute bottom-0 left-0 right-0 p-1.5 bg-gradient-to-t from-black/60 to-transparent opacity-0 hover:opacity-100 transition-opacity">
        <p className="text-xs text-white truncate">{item.original_filename}</p>
      </div>
    </button>
  )
}
