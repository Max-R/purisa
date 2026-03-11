/**
 * Types for scheduled jobs and execution history
 */

export interface ScheduledJob {
  id: number
  name: string
  platform: string
  queries: string[]
  cronExpression: string
  collectLimit: number
  analysisHours: number
  harvestComments: boolean
  enabled: boolean
  createdAt: string
  updatedAt: string
  nextRunAt: string | null
  lastExecution: JobExecution | null
}

export interface JobExecution {
  id: number
  jobId: number
  status: 'pending' | 'running' | 'success' | 'failed'
  startedAt: string | null
  completedAt: string | null
  durationSeconds: number | null
  postsCollected: number
  accountsDiscovered: number
  commentsCollected: number
  coordinationScore: number | null
  clustersDetected: number
  errorMessage: string | null
}

export interface CreateJobParams {
  name: string
  platform: string
  queries: string[]
  cronExpression: string
  collectLimit?: number
  analysisHours?: number
  harvestComments?: boolean
}

export interface UpdateJobParams {
  name?: string
  queries?: string[]
  cronExpression?: string
  collectLimit?: number
  analysisHours?: number
  harvestComments?: boolean
  enabled?: boolean
}

export interface JobEvent {
  event: 'job_started' | 'job_progress' | 'job_completed' | 'job_failed'
  data: Record<string, any>
}
