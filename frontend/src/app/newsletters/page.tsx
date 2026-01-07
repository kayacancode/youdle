'use client'

import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  Mail,
  Plus,
  RefreshCw,
  Clock,
  CheckCircle2,
  XCircle,
  Edit2
} from 'lucide-react'
import { api, Newsletter } from '@/lib/api'
import { cn, getStatusColor } from '@/lib/utils'
import { NewsletterCard } from '@/components/NewsletterCard'
import { CreateNewsletterModal } from '@/components/CreateNewsletterModal'
import { NewsletterPreviewModal } from '@/components/NewsletterPreviewModal'

const statusIcons = {
  draft: Edit2,
  scheduled: Clock,
  sent: CheckCircle2,
  failed: XCircle,
}

export default function NewslettersPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [selectedNewsletter, setSelectedNewsletter] = useState<Newsletter | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isPreviewModalOpen, setIsPreviewModalOpen] = useState(false)

  // Fetch newsletters
  const { data: newslettersData, isLoading, refetch } = useQuery({
    queryKey: ['newsletters', statusFilter],
    queryFn: () => api.listNewsletters({
      status: statusFilter || undefined,
      limit: 50
    }),
  })

  // Mutations
  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.deleteNewsletter(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['newsletters'] }),
  })

  const scheduleMutation = useMutation({
    mutationFn: (id: string) => api.scheduleNewsletter(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['newsletters'] }),
  })

  const sendMutation = useMutation({
    mutationFn: (id: string) => api.sendNewsletter(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['newsletters'] }),
  })

  const unscheduleMutation = useMutation({
    mutationFn: (id: string) => api.unscheduleNewsletter(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['newsletters'] }),
  })

  const autoCreateMutation = useMutation({
    mutationFn: () => api.autoCreateNewsletter(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['newsletters'] }),
  })

  const newsletters = newslettersData?.newsletters || []

  // Get counts for filter badges
  const allCount = newsletters.length
  const draftCount = newsletters.filter(n => n.status === 'draft').length
  const scheduledCount = newsletters.filter(n => n.status === 'scheduled').length
  const sentCount = newsletters.filter(n => n.status === 'sent').length
  const failedCount = newsletters.filter(n => n.status === 'failed').length

  const statusFilters = [
    { value: null, label: 'All', count: allCount, icon: Mail },
    { value: 'draft', label: 'Draft', count: draftCount, icon: Edit2 },
    { value: 'scheduled', label: 'Scheduled', count: scheduledCount, icon: Clock },
    { value: 'sent', label: 'Sent', count: sentCount, icon: CheckCircle2 },
    { value: 'failed', label: 'Failed', count: failedCount, icon: XCircle },
  ]

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-stone-900">Newsletters</h1>
          <p className="mt-2 text-stone-500">
            Create, preview, and schedule newsletter campaigns. Sends Thursdays at 9 AM EST.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => autoCreateMutation.mutate()}
            disabled={autoCreateMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm bg-stone-100 text-stone-700 hover:bg-stone-200 transition-all disabled:opacity-50"
          >
            <RefreshCw className={cn("w-4 h-4", autoCreateMutation.isPending && "animate-spin")} />
            Auto-Create
          </button>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm bg-youdle-600 text-white hover:bg-youdle-700 transition-all"
          >
            <Plus className="w-4 h-4" />
            Create Newsletter
          </button>
        </div>
      </div>

      {/* Status Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        {statusFilters.map((filter) => {
          const Icon = filter.icon
          const isActive = statusFilter === filter.value
          return (
            <button
              key={filter.value || 'all'}
              onClick={() => setStatusFilter(filter.value)}
              className={cn(
                'flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                isActive
                  ? filter.value ? getStatusColor(filter.value) : 'bg-youdle-100 text-youdle-700'
                  : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
              )}
            >
              <Icon className="w-4 h-4" />
              {filter.label}
              {filter.count > 0 && (
                <span className={cn(
                  'px-1.5 py-0.5 rounded text-xs',
                  isActive ? 'bg-white/30' : 'bg-stone-200'
                )}>
                  {filter.count}
                </span>
              )}
            </button>
          )
        })}
      </div>

      {/* Newsletter Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center py-16">
          <RefreshCw className="w-8 h-8 text-youdle-500 animate-spin" />
        </div>
      ) : newsletters.length === 0 ? (
        <div className="text-center py-16 rounded-2xl bg-stone-50 border border-stone-200">
          <Mail className="w-12 h-12 text-stone-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-stone-900 mb-2">No Newsletters Found</h3>
          <p className="text-stone-500 max-w-md mx-auto mb-4">
            {statusFilter
              ? `No ${statusFilter} newsletters yet.`
              : 'Create your first newsletter from published blog posts.'}
          </p>
          <button
            onClick={() => setIsCreateModalOpen(true)}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm bg-youdle-600 text-white hover:bg-youdle-700"
          >
            <Plus className="w-4 h-4" />
            Create Newsletter
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {newsletters.map((newsletter) => (
            <NewsletterCard
              key={newsletter.id}
              newsletter={newsletter}
              onPreview={() => {
                setSelectedNewsletter(newsletter)
                setIsPreviewModalOpen(true)
              }}
              onSchedule={() => scheduleMutation.mutate(newsletter.id)}
              onSend={() => sendMutation.mutate(newsletter.id)}
              onUnschedule={() => unscheduleMutation.mutate(newsletter.id)}
              onDelete={() => deleteMutation.mutate(newsletter.id)}
              isScheduling={scheduleMutation.isPending}
              isSending={sendMutation.isPending}
            />
          ))}
        </div>
      )}

      {/* Modals */}
      <CreateNewsletterModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSuccess={() => {
          setIsCreateModalOpen(false)
          queryClient.invalidateQueries({ queryKey: ['newsletters'] })
        }}
      />

      {selectedNewsletter && (
        <NewsletterPreviewModal
          isOpen={isPreviewModalOpen}
          newsletter={selectedNewsletter}
          onClose={() => {
            setIsPreviewModalOpen(false)
            setSelectedNewsletter(null)
          }}
        />
      )}
    </div>
  )
}
