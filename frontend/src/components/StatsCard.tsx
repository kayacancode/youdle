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
      'relative overflow-hidden rounded-2xl bg-white border border-stone-200 p-6 transition-all hover:shadow-lg hover:border-youdle-500/30',
      className
    )}>
      {/* Background decoration */}
      <div className="absolute -right-4 -top-4 w-24 h-24 rounded-full bg-gradient-to-br from-youdle-500/10 to-transparent" />

      <div className="relative">
        <div className="flex items-center justify-between">
          <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-youdle-500/10">
            <Icon className="w-6 h-6 text-youdle-600" />
          </div>

          {trend && (
            <div className={cn(
              'flex items-center gap-1 text-sm font-medium',
              trend.isPositive ? 'text-green-600' : 'text-red-600'
            )}>
              <span>{trend.isPositive ? '↑' : '↓'}</span>
              <span>{Math.abs(trend.value)}%</span>
            </div>
          )}
        </div>

        <div className="mt-4">
          <h3 className="text-sm font-medium text-stone-500">
            {title}
          </h3>
          <p className="mt-1 text-3xl font-bold text-stone-900">
            {value}
          </p>
          {subtitle && (
            <p className="mt-1 text-sm text-stone-500">
              {subtitle}
            </p>
          )}
        </div>
      </div>
    </div>
  )
}



