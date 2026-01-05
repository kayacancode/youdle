'use client'

import { useRealtime } from '@/lib/hooks/useRealtimeJobs'
import { cn, formatRelativeTime } from '@/lib/utils'
import { Radio, Wifi, WifiOff } from 'lucide-react'

interface RealtimeStatusProps {
  className?: string
}

export function RealtimeStatus({ className }: RealtimeStatusProps) {
  const { isConnected, lastJobUpdate, lastPostUpdate } = useRealtime()
  
  const lastUpdate = lastJobUpdate && lastPostUpdate
    ? new Date(Math.max(lastJobUpdate.getTime(), lastPostUpdate.getTime()))
    : lastJobUpdate || lastPostUpdate

  return (
    <div className={cn(
      'flex items-center gap-2 px-3 py-2 rounded-lg text-sm',
      isConnected 
        ? 'bg-green-50 dark:bg-green-900/20 text-green-700'
        : 'bg-midnight-100 text-stone-500',
      className
    )}>
      {isConnected ? (
        <>
          <Radio className="w-4 h-4 animate-pulse" />
          <span>Live</span>
          {lastUpdate && (
            <span className="text-xs opacity-75">
              • {formatRelativeTime(lastUpdate.toISOString())}
            </span>
          )}
        </>
      ) : (
        <>
          <WifiOff className="w-4 h-4" />
          <span>Offline</span>
        </>
      )}
    </div>
  )
}



