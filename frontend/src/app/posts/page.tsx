'use client'

import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { FileText, Filter, RefreshCw, ShoppingCart, AlertOctagon, Trash2 } from 'lucide-react'
import { api } from '@/lib/api'
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

  const deleteAllPostsMutation = useMutation({
    mutationFn: async () => {
      if (!posts || posts.length === 0) return
      await Promise.all(posts.map(post => api.deletePost(post.id)))
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['posts'] })
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
          <h1 className="text-3xl font-bold text-midnight-900 dark:text-white">
            Blog Posts
          </h1>
          <p className="mt-2 text-midnight-500 dark:text-midnight-400">
            View and manage generated blog posts. Update status and copy HTML for publishing.
          </p>
        </div>
        {posts && posts.length > 0 && (
          <button
            onClick={handleDeleteAll}
            disabled={deleteAllPostsMutation.isPending}
            className="flex items-center gap-2 px-4 py-2 rounded-xl font-medium text-sm transition-all bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 hover:bg-red-200 dark:hover:bg-red-900/50 disabled:opacity-50 disabled:cursor-not-allowed"
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

      {/* Filters */}
      <div className="rounded-2xl bg-white dark:bg-midnight-800/50 border border-midnight-200 dark:border-midnight-700 p-6">
        <div className="flex flex-wrap items-center gap-4">
          {/* Status Filter */}
          <div>
            <label className="block text-xs font-medium text-midnight-500 dark:text-midnight-400 mb-2">
              Status
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setStatusFilter(null)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  !statusFilter
                    ? 'bg-youdle-100 dark:bg-youdle-900/30 text-youdle-700 dark:text-youdle-300'
                    : 'bg-midnight-100 dark:bg-midnight-800 text-midnight-600 dark:text-midnight-400 hover:bg-midnight-200 dark:hover:bg-midnight-700'
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
                      : 'bg-midnight-100 dark:bg-midnight-800 text-midnight-600 dark:text-midnight-400 hover:bg-midnight-200 dark:hover:bg-midnight-700'
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
            <label className="block text-xs font-medium text-midnight-500 dark:text-midnight-400 mb-2">
              Category
            </label>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setCategoryFilter(null)}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all',
                  !categoryFilter
                    ? 'bg-youdle-100 dark:bg-youdle-900/30 text-youdle-700 dark:text-youdle-300'
                    : 'bg-midnight-100 dark:bg-midnight-800 text-midnight-600 dark:text-midnight-400 hover:bg-midnight-200 dark:hover:bg-midnight-700'
                )}
              >
                All
              </button>
              <button
                onClick={() => setCategoryFilter('SHOPPERS')}
                className={cn(
                  'px-3 py-1.5 rounded-lg text-sm font-medium transition-all flex items-center gap-1',
                  categoryFilter === 'SHOPPERS'
                    ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300'
                    : 'bg-midnight-100 dark:bg-midnight-800 text-midnight-600 dark:text-midnight-400 hover:bg-midnight-200 dark:hover:bg-midnight-700'
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
                    ? 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300'
                    : 'bg-midnight-100 dark:bg-midnight-800 text-midnight-600 dark:text-midnight-400 hover:bg-midnight-200 dark:hover:bg-midnight-700'
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
          <RefreshCw className="w-8 h-8 text-youdle-500 animate-spin" />
        </div>
      )}

      {/* Error State */}
      {error && (
        <div className="p-4 rounded-xl bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800">
          <p className="text-red-800 dark:text-red-200">
            Error: {error instanceof Error ? error.message : 'Failed to load posts'}
          </p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && posts?.length === 0 && (
        <div className="text-center py-16 rounded-2xl bg-white dark:bg-midnight-800/50 border border-midnight-200 dark:border-midnight-700">
          <FileText className="w-12 h-12 text-midnight-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-midnight-900 dark:text-white mb-2">
            No Posts Found
          </h3>
          <p className="text-midnight-500 dark:text-midnight-400 max-w-md mx-auto">
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
            />
          ))}
        </div>
      )}
    </div>
  )
}



