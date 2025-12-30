'use client'

import { cn } from '@/lib/utils'
import { LucideIcon } from 'lucide-react'

interface StatsCardProps {
  title: string
  value: string | number
  subtitle?: string
  icon: LucideIcon
  trend?: {
    value: number
    isPositive: boolean
  }
  className?: string
}

export function StatsCard({ 
  title, 
  value, 
  subtitle, 
  icon: Icon, 
  trend,
  className 
}: StatsCardProps) {
  return (
    <div className={cn(
      'relative overflow-hidden rounded-2xl bg-white dark:bg-midnight-800/50 border border-midnight-200 dark:border-midnight-700 p-6 transition-all hover:shadow-lg hover:border-youdle-500/30',
      className
    )}>
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-gradient-to-br from-youdle-500/10 to-transparent" />
      
      <div className="relative">
        <div className="flex items-center justify-between">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-youdle-500/10 dark:bg-youdle-500/20">
            <Icon className="w-6 h-6 text-youdle-600 dark:text-youdle-400" />
          </div>
          
          {trend && (
            <div className={cn(
              'flex items-center gap-1 text-sm font-medium',
              trend.isPositive ? 'text-green-600 dark:text-green-400' : 'text-red-600 dark:text-red-400'
            )}>
              <span>{trend.isPositive ? '↑' : '↓'}</span>
              <span>{Math.abs(trend.value)}%</span>
            </div>
          )}
        </div>
        
        <div className="mt-4">
          <h3 className="text-sm font-medium text-midnight-500 dark:text-midnight-400">
            {title}
          </h3>
          <p className="mt-1 text-3xl font-bold text-midnight-900 dark:text-white">
            {value}
          </p>
          {subtitle && (
            <p className="mt-1 text-sm text-midnight-500 dark:text-midnight-400">
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}



