'use client'

import { useEffect, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { subscribeToJobs, subscribeToPosts, Job, BlogPost } from '../supabase'

/**
 * Hook for subscribing to real-time job updates
 */
export function useRealtimeJobs() {
  const queryClient = useQueryClient()
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    let channel: ReturnType<typeof subscribeToJobs> | null = null

    try {
      channel = subscribeToJobs((payload) => {
        setLastUpdate(new Date())
        
        // Invalidate relevant queries
        queryClient.invalidateQueries({ queryKey: ['jobs'] })
        queryClient.invalidateQueries({ queryKey: ['recentJobs'] })
        queryClient.invalidateQueries({ queryKey: ['stats'] })
        
        // If a specific job was updated, invalidate its details
        if (payload.new?.id) {
          queryClient.invalidateQueries({ queryKey: ['jobDetails', payload.new.id] })
        }
      })
      
      setIsConnected(true)
    } catch (error) {
      console.error('Failed to subscribe to job updates:', error)
      setIsConnected(false)
    }

    return () => {
      if (channel) {
        channel.unsubscribe()
        setIsConnected(false)
      }
    }
  }, [queryClient])

  return { isConnected, lastUpdate }
}

/**
 * Hook for subscribing to real-time post updates
 */
export function useRealtimePosts() {
  const queryClient = useQueryClient()
  const [isConnected, setIsConnected] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null)

  useEffect(() => {
    let channel: ReturnType<typeof subscribeToPosts> | null = null

    try {
      channel = subscribeToPosts((payload) => {
        setLastUpdate(new Date())
        
        // Invalidate relevant queries
        queryClient.invalidateQueries({ queryKey: ['posts'] })
        queryClient.invalidateQueries({ queryKey: ['reviewPosts'] })
        queryClient.invalidateQueries({ queryKey: ['stats'] })
        
        // If a specific post was updated, invalidate its details
        if (payload.new?.id) {
          queryClient.invalidateQueries({ queryKey: ['postDetails', payload.new.id] })
        }
      })
      
      setIsConnected(true)
    } catch (error) {
      console.error('Failed to subscribe to post updates:', error)
      setIsConnected(false)
    }

    return () => {
      if (channel) {
        channel.unsubscribe()
        setIsConnected(false)
      }
    }
  }, [queryClient])

  return { isConnected, lastUpdate }
}

/**
 * Combined hook for all real-time subscriptions
 */
export function useRealtime() {
  const jobs = useRealtimeJobs()
  const posts = useRealtimePosts()

  return {
    isConnected: jobs.isConnected || posts.isConnected,
    jobsConnected: jobs.isConnected,
    postsConnected: posts.isConnected,
    lastJobUpdate: jobs.lastUpdate,
    lastPostUpdate: posts.lastUpdate,
  }
}



