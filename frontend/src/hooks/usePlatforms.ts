/**
 * Platforms hook for fetching available platforms
 */
import { useState, useEffect, useCallback } from 'react'
import { apiClient } from '../api/client'

interface UsePlatformsResult {
  platforms: string[]
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

export function usePlatforms(): UsePlatformsResult {
  const [platforms, setPlatforms] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchPlatforms = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await apiClient.getPlatformStatus()
      setPlatforms(response.available_platforms || [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      console.error('Error fetching platforms:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchPlatforms()
  }, [fetchPlatforms])

  return {
    platforms,
    loading,
    error,
    refetch: fetchPlatforms
  }
}
