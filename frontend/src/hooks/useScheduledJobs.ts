/**
 * Hook for managing scheduled jobs (CRUD + run now)
 */
import { useState, useCallback } from 'react'
import type { ScheduledJob, CreateJobParams, UpdateJobParams } from '../types/schedule'
import { apiClient } from '../api/client'

interface UseScheduledJobsResult {
  jobs: ScheduledJob[]
  loading: boolean
  error: string | null
  fetchJobs: (platform?: string) => Promise<void>
  createJob: (params: CreateJobParams) => Promise<ScheduledJob>
  updateJob: (jobId: number, params: UpdateJobParams) => Promise<ScheduledJob>
  deleteJob: (jobId: number) => Promise<void>
  runJobNow: (jobId: number) => Promise<void>
}

export function useScheduledJobs(): UseScheduledJobsResult {
  const [jobs, setJobs] = useState<ScheduledJob[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const fetchJobs = useCallback(async (platform?: string) => {
    setLoading(true)
    setError(null)

    try {
      const result = await apiClient.getJobs(platform)
      setJobs(result)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to fetch jobs')
      console.error('Error fetching jobs:', e)
    } finally {
      setLoading(false)
    }
  }, [])

  const createJob = useCallback(async (params: CreateJobParams): Promise<ScheduledJob> => {
    setError(null)
    try {
      const newJob = await apiClient.createJob(params)
      // Optimistic: append to list
      setJobs(prev => [...prev, newJob])
      return newJob
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Failed to create job'
      setError(msg)
      throw new Error(msg)
    }
  }, [])

  const updateJob = useCallback(async (jobId: number, params: UpdateJobParams): Promise<ScheduledJob> => {
    setError(null)
    try {
      const updated = await apiClient.updateJob(jobId, params)
      // Optimistic: replace in list
      setJobs(prev => prev.map(j => j.id === jobId ? updated : j))
      return updated
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Failed to update job'
      setError(msg)
      throw new Error(msg)
    }
  }, [])

  const deleteJob = useCallback(async (jobId: number) => {
    setError(null)
    try {
      await apiClient.deleteJob(jobId)
      // Optimistic: remove from list
      setJobs(prev => prev.filter(j => j.id !== jobId))
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Failed to delete job'
      setError(msg)
      throw new Error(msg)
    }
  }, [])

  const runJobNow = useCallback(async (jobId: number) => {
    setError(null)
    try {
      await apiClient.runJobNow(jobId)
    } catch (e: any) {
      const msg = e.response?.data?.detail || e.message || 'Failed to trigger job'
      setError(msg)
      throw new Error(msg)
    }
  }, [])

  return {
    jobs,
    loading,
    error,
    fetchJobs,
    createJob,
    updateJob,
    deleteJob,
    runJobNow,
  }
}
