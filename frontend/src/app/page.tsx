'use client'

import { useQuery } from '@tanstack/react-query'
import { 
  FileText, 
  Activity, 
  CheckCircle2, 
  AlertTriangle,
  ShoppingCart,
  AlertOctagon
} from 'lucide-react'
import { api, SystemStats } from '@/lib/api'
import { StatsCard } from '@/components/StatsCard'
import { RunStatus } from '@/components/RunStatus'
import { QuickActions } from '@/components/QuickActions'
import { formatNumber } from '@/lib/utils'

export default function DashboardPage() {
  // Fetch system stats
  const { data: stats, isLoading: statsLoading, refetch: refetchStats } = useQuery<SystemStats>({
    queryKey: ['stats'],
    queryFn: () => api.getStats(),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  // Fetch recent jobs
  const { data: jobsData, isLoading: jobsLoading, refetch: refetchJobs } = useQuery({
    queryKey: ['recentJobs'],
    queryFn: async () => {
      const data = await api.listJobs({ limit: 5 })
      // Sort jobs by started_at or completed_at, latest first
      const sortedJobs = [...(data.jobs || [])].sort((a, b) => {
        const aDate = new Date(a.started_at || a.completed_at || 0).getTime()
        const bDate = new Date(b.started_at || b.completed_at || 0).getTime()
        return bDate - aDate
      })
      return { ...data, jobs: sortedJobs }
    },
    refetchInterval: 10000, // Refresh every 10 seconds
  })

  const handleSearchPreview = () => {
    window.location.href = '/articles'
  }

  const handleStartGeneration = (jobId: string) => {
    refetchJobs()
    refetchStats()
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-midnight-900 dark:text-white">
          Dashboard
        </h1>
        <p className="mt-2 text-midnight-500 dark:text-midnight-400">
          Monitor your blog generation pipeline and manage content.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 stagger-children">
        <StatsCard
          title="Total Posts"
          value={statsLoading ? '...' : formatNumber(stats?.posts.total || 0)}
          subtitle={`${stats?.posts.draft || 0} drafts`}
          icon={FileText}
        />
        <StatsCard
          title="Running Jobs"
          value={statsLoading ? '...' : stats?.jobs.running || 0}
          subtitle={`${stats?.jobs.completed || 0} completed`}
          icon={Activity}
        />
        <StatsCard
          title="Shoppers Articles"
          value={statsLoading ? '...' : formatNumber(stats?.posts.by_category?.shoppers || 0)}
          icon={ShoppingCart}
        />
        <StatsCard
          title="Recall Alerts"
          value={statsLoading ? '...' : formatNumber(stats?.posts.by_category?.recall || 0)}
          icon={AlertOctagon}
        />
      </div>

      {/* Status breakdown */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="flex items-center gap-4 p-4 rounded-xl bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800">
          <CheckCircle2 className="w-8 h-8 text-green-600 dark:text-green-400" />
          <div>
            <p className="text-sm text-green-700 dark:text-green-300 font-medium">Published</p>
            <p className="text-2xl font-bold text-green-800 dark:text-green-200">
              {stats?.posts.published || 0}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 p-4 rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800">
          <Activity className="w-8 h-8 text-purple-600 dark:text-purple-400" />
          <div>
            <p className="text-sm text-purple-700 dark:text-purple-300 font-medium">Reviewed</p>
            <p className="text-2xl font-bold text-purple-800 dark:text-purple-200">
              {stats?.posts.reviewed || 0}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-4 p-4 rounded-xl bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800">
          <AlertTriangle className="w-8 h-8 text-amber-600 dark:text-amber-400" />
          <div>
            <p className="text-sm text-amber-700 dark:text-amber-300 font-medium">Failed Jobs</p>
            <p className="text-2xl font-bold text-amber-800 dark:text-amber-200">
              {stats?.jobs.failed || 0}
            </p>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <QuickActions 
        onSearchPreview={handleSearchPreview}
        onStartGeneration={handleStartGeneration}
      />

      {/* Recent Jobs */}
      <RunStatus 
        jobs={jobsData?.jobs || []}
      />

      {/* API Status */}
      <div className="rounded-2xl bg-white dark:bg-midnight-800/50 border border-midnight-200 dark:border-midnight-700 p-6">
        <h3 className="text-lg font-semibold text-midnight-900 dark:text-white mb-4">System Status</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="flex items-center gap-3 p-3 rounded-xl bg-midnight-50 dark:bg-midnight-900/50">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <div>
              <p className="text-sm font-medium text-midnight-900 dark:text-white">FastAPI Backend</p>
              <p className="text-xs text-midnight-500 dark:text-midnight-400">http://localhost:8000</p>
            </div>
          </div>
          <div className="flex items-center gap-3 p-3 rounded-xl bg-midnight-50 dark:bg-midnight-900/50">
            <div className="w-3 h-3 rounded-full bg-green-500 animate-pulse" />
            <div>
              <p className="text-sm font-medium text-midnight-900 dark:text-white">Supabase</p>
              <p className="text-xs text-midnight-500 dark:text-midnight-400">Connected</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}



