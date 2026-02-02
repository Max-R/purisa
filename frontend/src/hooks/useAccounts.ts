/**
 * Accounts hook for fetching all and flagged accounts with pagination
 */
import { useState, useCallback } from 'react'
import type { AccountWithScore } from '../types/account'
import { apiClient } from '../api/client'

interface UseAccountsResult {
  allAccounts: AccountWithScore[]
  flaggedAccounts: AccountWithScore[]
  allAccountsTotal: number
  flaggedAccountsTotal: number
  loading: boolean
  error: string | null
  fetchAll: (platform?: string, limit?: number, offset?: number, includeCommentStats?: boolean) => Promise<void>
  fetchFlagged: (platform?: string, limit?: number, offset?: number, includeCommentStats?: boolean) => Promise<void>
  refresh: () => Promise<void>
}

export function useAccounts(): UseAccountsResult {
  const [allAccounts, setAllAccounts] = useState<AccountWithScore[]>([])
  const [flaggedAccounts, setFlaggedAccounts] = useState<AccountWithScore[]>([])
  const [allAccountsTotal, setAllAccountsTotal] = useState(0)
  const [flaggedAccountsTotal, setFlaggedAccountsTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchAll = useCallback(async (
    platform?: string,
    limit: number = 50,
    offset: number = 0,
    includeCommentStats: boolean = true
  ) => {
    setLoading(true)
    setError(null)

    try {
      const result = await apiClient.getAllAccounts(platform, limit, offset, includeCommentStats)
      setAllAccounts(result.accounts)
      setAllAccountsTotal(result.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      console.error('Error fetching all accounts:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  const fetchFlagged = useCallback(async (
    platform?: string,
    limit: number = 50,
    offset: number = 0,
    includeCommentStats: boolean = true
  ) => {
    setLoading(true)
    setError(null)

    try {
      const result = await apiClient.getFlaggedAccounts(platform, limit, offset, includeCommentStats)
      setFlaggedAccounts(result.accounts)
      setFlaggedAccountsTotal(result.total)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
      console.error('Error fetching flagged accounts:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  const refresh = useCallback(async () => {
    await Promise.all([fetchAll(), fetchFlagged()])
  }, [fetchAll, fetchFlagged])

  return {
    allAccounts,
    flaggedAccounts,
    allAccountsTotal,
    flaggedAccountsTotal,
    loading,
    error,
    fetchAll,
    fetchFlagged,
    refresh
  }
}
