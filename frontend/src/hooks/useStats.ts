/**
 * Stats hook for fetching overview and comment statistics
 */
import { useState, useEffect, useCallback } from 'react'
import type { Stats, CommentStats } from '../types/detection'
import { apiClient } from '../api/client'

interface UseStatsResult {
  stats: Stats | null
  commentStats: CommentStats | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useStats(platform?: string): UseStatsResult {
  const [stats, setStats] = useState<Stats | null>(null)
  const [commentStats, setCommentStats] = useState<CommentStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const [coreStats, comments] = await Promise.all([
        apiClient.getStats(platform),
        apiClient.getCommentStats(platform).catch(() => null)
      ])
      setStats(coreStats)
      setCommentStats(comments)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      console.error('Error fetching stats:', e)
    } finally {
      setLoading(false)
    }
  }, [platform])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    stats,
    commentStats,
    loading,
    error,
    refetch: fetchData
  }
}
