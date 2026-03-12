/**
 * Hook for fetching coordination detection data.
 *
 * Loads timeline, clusters, stats, and spikes for a given platform.
 * Provides refetch() for manual refresh (e.g. after SSE job_completed).
 */
import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../api/client'
import type { TimelineResponse } from '../types/coordination'
import type { ClustersResponse } from '../types/coordination'
import type { CoordinationStats } from '../types/coordination'
import type { SpikesResponse } from '../types/coordination'

interface UseCoordinationResult {
  timeline: TimelineResponse | null
  clusters: ClustersResponse | null
  stats: CoordinationStats | null
  spikes: SpikesResponse | null
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function useCoordination(platform?: string, query?: string): UseCoordinationResult {
  const [timeline, setTimeline] = useState<TimelineResponse | null>(null)
  const [clusters, setClusters] = useState<ClustersResponse | null>(null)
  const [stats, setStats] = useState<CoordinationStats | null>(null)
  const [spikes, setSpikes] = useState<SpikesResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchData = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      // Fetch all coordination data in parallel
      // Stats doesn't require a platform, but others do
      // Pass optional query filter to scope results
      const q = query || undefined
      const results = await Promise.allSettled([
        platform ? apiClient.getCoordinationTimeline(platform, 168, q) : Promise.resolve(null),
        platform ? apiClient.getCoordinationClusters(platform, 24, q) : Promise.resolve(null),
        apiClient.getCoordinationStats(platform || undefined, q),
        platform ? apiClient.getCoordinationSpikes(platform, 168, q) : Promise.resolve(null),
      ])

      const [timelineResult, clustersResult, statsResult, spikesResult] = results

      setTimeline(timelineResult.status === 'fulfilled' ? timelineResult.value : null)
      setClusters(clustersResult.status === 'fulfilled' ? clustersResult.value : null)
      setStats(statsResult.status === 'fulfilled' ? statsResult.value : null)
      setSpikes(spikesResult.status === 'fulfilled' ? spikesResult.value : null)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch coordination data')
      console.error('Error fetching coordination data:', e)
    } finally {
      setLoading(false)
    }
  }, [platform, query])

  useEffect(() => {
    fetchData()
  }, [fetchData])

  return {
    timeline,
    clusters,
    stats,
    spikes,
    loading,
    error,
    refetch: fetchData,
  }
}
