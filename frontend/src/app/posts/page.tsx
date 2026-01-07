'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Filter, RefreshCw, ShoppingCart, AlertOctagon, Trash2, Globe } from 'lucide-react'
import { api, type BlogPostUpdate } from '@/lib/api'
import { BlogPostPreview } from '@/components/BlogPostPreview'
import { cn, getStatusColor } from '@/lib/utils'

export default function PostsPage() {
  const queryClient = useQueryClient()
  const [statusFilter, setStatusFilter] = useState<string | null>(null)
  const [categoryFilter, setCategoryFilter] = useState<string | null>(null)

  const { data: posts, isLoading, error } = useQuery({
    queryKey: ['posts', statusFilter, categoryFilter],
    queryFn: () => api.getPosts({ 
      status: statusFilter || undefined, 
      category: categoryFilter || undefined,
      limit: 50 
    }),
  })

  const updateStatusMutation = useMutation({
    mutationFn: ({ postId, status }: { postId: string; status: string }) =>
      api.updatePostStatus(postId, status),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const deletePostMutation = useMutation({
    mutationFn: (postId: string) => api.deletePost(postId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const updatePostMutation = useMutation({
    mutationFn: ({ postId, updates }: { postId: string; updates: BlogPostUpdate }) =>
      api.updatePost(postId, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const publishToBloggerMutation = useMutation({
    mutationFn: (postId: string) => api.publishToBlogger(postId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const unpublishFromBloggerMutation = useMutation({
    mutationFn: (postId: string) => api.unpublishFromBlogger(postId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const deleteAllPostsMutation = useMutation({
    mutationFn: async () => {
      if (!posts || posts.length === 0) return
      await Promise.all(posts.map(post => api.deletePost(post.id)))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
    },
  })

  const syncWithBloggerMutation = useMutation({
    mutationFn: () => api.syncWithBlogger(),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
      alert(`Sync complete! ${data.synced_count} posts updated.`)
    },
    onError: (error) => {
      alert(`Sync failed: ${error instanceof Error ? error.message : 'Unknown error'}`)
    },
  })

  const handleStatusChange = (postId: string, status: string) => {
    updateStatusMutation.mutate({ postId, status })
  }

  const handleDelete = (postId: string) => {
    if (confirm('Are you sure you want to delete this post?')) {
      deletePostMutation.mutate(postId)
    }
  }

  const handleEdit = async (postId: string, updates: BlogPostUpdate) => {
    await updatePostMutation.mutateAsync({ postId, updates })
  }

  const handlePublish = async (postId: string) => {
    await publishToBloggerMutation.mutateAsync(postId)
  }

  const handleUnpublish = async (postId: string) => {
    await unpublishFromBloggerMutation.mutateAsync(postId)
  }

  const handleDeleteAll = () => {
    if (confirm(`Are you sure you want to delete all ${posts?.length || 0} posts? This action cannot be undone.`)) {
      deleteAllPostsMutation.mutate()
    }
  }

  // Count posts by status
  const statusCounts = posts?.reduce((acc, post) => {
    acc[post.status] = (acc[post.status] || 0) + 1
    return acc
  }, {} as Record<string, number>) || {}

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-5xl font-display font-light text-stone-900 tracking-tight">
            Blog Posts
          </h1>
          <p className="mt-2 text-lg text-stone-500 font-light">
            View and manage generated blog posts. Update status and copy HTML for publishing.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => syncWithBloggerMutation.mutate()}
            disabled={syncWithBloggerMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all bg-blue-100 text-blue-700 hover:bg-blue-200 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncWithBloggerMutation.isPending ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <Globe className="w-4 h-4" />
            )}
            Sync with Blogger
          </button>
          {posts && posts.length > 0 && (
            <button
              onClick={handleDeleteAll}
              disabled={deleteAllPostsMutation.isPending}
              className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all bg-red-100 text-red-700 hover:bg-red-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {deleteAllPostsMutation.isPending ? (
                <RefreshCw className="w-4 h-4 animate-spin" />
              ) : (
                <Trash2 className="w-4 h-4" />
              )}
              Delete All
            </button>
          )}
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-2xl bg-stone-50/50 border border-stone-200 p-8">
        <div className="flex flex-wrap items-center gap-4">
          {/* Status Filter */}
          <div>
            <label className="block text-xs font-medium text-stone-500 mb-2">
              Status
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setStatusFilter(null)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  !statusFilter
                    ? 'bg-accent-100 text-accent-700'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                )}
              >
                All
              </button>
              {['draft', 'reviewed', 'published'].map(status => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status)}
                  className={cn(
                    'px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1',
                    statusFilter === status
                      ? getStatusColor(status)
                      : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                  )}
                >
                  {status.charAt(0).toUpperCase() + status.slice(1)}
                  {statusCounts[status] && (
                    <span className="text-xs opacity-75">({statusCounts[status]})</span>
                  )}
                </button>
              ))}
            </div>
          </div>

          {/* Category Filter */}
          <div>
            <label className="block text-xs font-medium text-stone-500 mb-2">
              Category
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCategoryFilter(null)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  !categoryFilter
                    ? 'bg-accent-100 text-accent-700'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                )}
              >
                All
              </button>
              <button
                onClick={() => setCategoryFilter('SHOPPERS')}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1',
                  categoryFilter === 'SHOPPERS'
                    ? 'bg-green-100 text-green-700'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                )}
              >
                <ShoppingCart className="w-4 h-4" />
                Shoppers
              </button>
              <button
                onClick={() => setCategoryFilter('RECALL')}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1',
                  categoryFilter === 'RECALL'
                    ? 'bg-amber-100 text-amber-700'
                    : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                )}
              >
                <AlertOctagon className="w-4 h-4" />
                Recall
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="flex items-center justify-center py-16">
          <RefreshCw className="w-8 h-8 text-accent-500 animate-spin" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 border border-red-200">
          <p className="text-red-800">
            Error: {error instanceof Error ? error.message : 'Failed to load posts'}
          </p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && posts?.length === 0 && (
        <div className="text-center py-16 rounded-2xl bg-stone-50/50 border border-stone-200">
          <FileText className="w-12 h-12 text-stone-400 mx-auto mb-4" />
          <h3 className="text-xl font-display font-semibold text-stone-900 mb-2">
            No Posts Found
          </h3>
          <p className="text-stone-500 max-w-md mx-auto">
            No blog posts match your current filters. Try adjusting the filters or generate new posts.
          </p>
        </div>
      )}

      {/* Posts Grid */}
      {posts && posts.length > 0 && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 stagger-children">
          {posts.map((post) => (
            <BlogPostPreview
              key={post.id}
              post={post}
              onStatusChange={handleStatusChange}
              onDelete={handleDelete}
              onEdit={handleEdit}
              onPublish={handlePublish}
              onUnpublish={handleUnpublish}
            />
          ))}
        </div>
      )}
    </div>
  )
}



