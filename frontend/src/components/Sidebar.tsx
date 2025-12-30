'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { 
  LayoutDashboard, 
  Search, 
  FileText, 
  CheckSquare, 
  Settings,
  Activity,
  Zap
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Articles', href: '/articles', icon: Search },
  { name: 'Blog Posts', href: '/posts', icon: FileText },
  { name: 'Review', href: '/review', icon: CheckSquare },
  { name: 'Jobs', href: '/jobs', icon: Activity },
  { name: 'Settings', href: '/settings', icon: Settings },
]

export function Sidebar() {
  const pathname = usePathname()

  return (
    <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-midnight-900 border-r border-midnight-800">
      {/* Logo */}
      <div className="flex items-center gap-3 px-6 py-5 border-b border-midnight-800">
        <div className="flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-br from-youdle-500 to-youdle-600 shadow-lg shadow-youdle-500/25">
          <Zap className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-white tracking-tight">Youdle</h1>
          <p className="text-xs text-midnight-400">Blog Agent Dashboard</p>
        </div>
      </div>

      {/* Navigation */}
      <nav className="px-3 py-4 space-y-1">
        {navigation.map((item) => {
          const isActive = pathname === item.href || 
            (item.href !== '/' && pathname.startsWith(item.href))
          
          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-150',
                isActive
                  ? 'bg-youdle-500/10 text-youdle-400 shadow-sm'
                  : 'text-midnight-400 hover:text-white hover:bg-midnight-800'
              )}
            >
              <item.icon className={cn(
                'w-5 h-5 transition-colors',
                isActive ? 'text-youdle-400' : 'text-midnight-500'
              )} />
              {item.name}
            </Link>
          )
        })}
      </nav>

      {/* Status indicator */}
      <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-midnight-800">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-midnight-800/50">
          <div className="w-2 h-2 rounded-full bg-youdle-500 animate-pulse" />
          <span className="text-xs text-midnight-400">System Online</span>
        </div>
        <p className="text-xs text-midnight-500 mt-2 px-3">Real-time updates enabled</p>
      </div>
    </aside>
  )
}

