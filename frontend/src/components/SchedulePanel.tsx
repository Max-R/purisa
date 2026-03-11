/**
 * SchedulePanel — CRUD UI for scheduled collection/analysis jobs
 * with live SSE status updates.
 */
import { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Clock,
  Plus,
  Play,
  Trash2,
  Pencil,
  Loader2,
  AlertCircle,
  X,
  History,
} from 'lucide-react'
import { useScheduledJobs } from '../hooks/useScheduledJobs'
import { useJobEvents } from '../hooks/useJobEvents'
import CronInput from './CronInput'
import JobHistory from './JobHistory'
import type { CreateJobParams, UpdateJobParams, ScheduledJob, JobEvent } from '../types/schedule'

interface SchedulePanelProps {
  platforms: string[]
  onJobComplete?: () => void
}

const limitOptions = [50, 100, 250, 500, 1000]
const analysisHoursOptions = [1, 3, 6, 12, 24, 48]

function formatNextRun(iso: string | null): string {
  if (!iso) return 'Not scheduled'
  try {
    const date = new Date(iso)
    const now = new Date()
    const diffMs = date.getTime() - now.getTime()
    if (diffMs < 0) return 'Overdue'
    if (diffMs < 60_000) return 'Less than a minute'
    if (diffMs < 3_600_000) return `${Math.round(diffMs / 60_000)}m`
    if (diffMs < 86_400_000) return `${Math.round(diffMs / 3_600_000)}h`
    return `${Math.round(diffMs / 86_400_000)}d`
  } catch {
    return iso
  }
}

function LastStatusBadge({ job }: { job: ScheduledJob }) {
  const exec = job.lastExecution
  if (!exec) return <Badge variant="secondary">Never run</Badge>

  switch (exec.status) {
    case 'success':
      return <Badge variant="success">Success</Badge>
    case 'failed':
      return <Badge variant="destructive">Failed</Badge>
    case 'running':
      return (
        <Badge variant="warning" className="flex items-center gap-1">
          <Loader2 className="h-3 w-3 animate-spin" />
          Running
        </Badge>
      )
    default:
      return <Badge variant="secondary">{exec.status}</Badge>
  }
}

export default function SchedulePanel({ platforms, onJobComplete }: SchedulePanelProps) {
  const { jobs, loading, error, fetchJobs, createJob, updateJob, deleteJob, runJobNow } = useScheduledJobs()

  // SSE events
  const handleEvent = useCallback((event: JobEvent) => {
    if (event.event === 'job_completed' || event.event === 'job_failed') {
      // Refetch jobs to pick up latest execution data
      fetchJobs()
      onJobComplete?.()
    }
  }, [fetchJobs, onJobComplete])

  const { connected } = useJobEvents(handleEvent)

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingJob, setEditingJob] = useState<ScheduledJob | null>(null)
  const [historyJobId, setHistoryJobId] = useState<number | null>(null)

  // Form state
  const [formName, setFormName] = useState('')
  const [formPlatform, setFormPlatform] = useState(platforms[0] || 'bluesky')
  const [formQueries, setFormQueries] = useState<string[]>([])
  const [formQueryInput, setFormQueryInput] = useState('')
  const [formCron, setFormCron] = useState('0 */6 * * *')
  const [formLimit, setFormLimit] = useState(100)
  const [formAnalysisHours, setFormAnalysisHours] = useState(6)
  const [formHarvestComments, setFormHarvestComments] = useState(true)
  const [formSubmitting, setFormSubmitting] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)

  // Running state for individual job run buttons
  const [runningJobId, setRunningJobId] = useState<number | null>(null)

  // Load jobs on mount
  useEffect(() => {
    fetchJobs()
  }, [fetchJobs])

  // Reset form
  const resetForm = useCallback(() => {
    setFormName('')
    setFormPlatform(platforms[0] || 'bluesky')
    setFormQueries([])
    setFormQueryInput('')
    setFormCron('0 */6 * * *')
    setFormLimit(100)
    setFormAnalysisHours(6)
    setFormHarvestComments(true)
    setFormError(null)
    setEditingJob(null)
  }, [platforms])

  const openCreate = () => {
    resetForm()
    setDialogOpen(true)
  }

  const openEdit = (job: ScheduledJob) => {
    setEditingJob(job)
    setFormName(job.name)
    setFormPlatform(job.platform)
    setFormQueries([...job.queries])
    setFormQueryInput('')
    setFormCron(job.cronExpression)
    setFormLimit(job.collectLimit)
    setFormAnalysisHours(job.analysisHours)
    setFormHarvestComments(job.harvestComments)
    setFormError(null)
    setDialogOpen(true)
  }

  // Query chips
  const addQuery = () => {
    const trimmed = formQueryInput.trim()
    if (trimmed && !formQueries.includes(trimmed)) {
      setFormQueries([...formQueries, trimmed])
      setFormQueryInput('')
    }
  }

  const removeQuery = (q: string) => {
    setFormQueries(formQueries.filter(x => x !== q))
  }

  const handleQueryKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      e.preventDefault()
      addQuery()
    }
  }

  // Submit form
  const handleSubmit = async () => {
    if (!formName.trim()) {
      setFormError('Name is required')
      return
    }
    if (formQueries.length === 0) {
      setFormError('At least one search query is required')
      return
    }
    if (!formCron.trim()) {
      setFormError('Cron expression is required')
      return
    }

    setFormSubmitting(true)
    setFormError(null)

    try {
      if (editingJob) {
        const params: UpdateJobParams = {
          name: formName,
          queries: formQueries,
          cronExpression: formCron,
          collectLimit: formLimit,
          analysisHours: formAnalysisHours,
          harvestComments: formHarvestComments,
        }
        await updateJob(editingJob.id, params)
      } else {
        const params: CreateJobParams = {
          name: formName,
          platform: formPlatform,
          queries: formQueries,
          cronExpression: formCron,
          collectLimit: formLimit,
          analysisHours: formAnalysisHours,
          harvestComments: formHarvestComments,
        }
        await createJob(params)
      }
      setDialogOpen(false)
      resetForm()
    } catch (e: any) {
      setFormError(e.message || 'Failed to save job')
    } finally {
      setFormSubmitting(false)
    }
  }

  // Run now
  const handleRunNow = async (jobId: number) => {
    setRunningJobId(jobId)
    try {
      await runJobNow(jobId)
      // SSE will notify us when it completes
    } catch (e) {
      console.error('Failed to run job:', e)
    } finally {
      // Keep the spinner briefly — SSE will update the status
      setTimeout(() => setRunningJobId(null), 1000)
    }
  }

  // Toggle enabled
  const handleToggleEnabled = async (job: ScheduledJob) => {
    try {
      await updateJob(job.id, { enabled: !job.enabled })
    } catch (e) {
      console.error('Failed to toggle job:', e)
    }
  }

  // Delete
  const handleDelete = async (jobId: number) => {
    try {
      await deleteJob(jobId)
    } catch (e) {
      console.error('Failed to delete job:', e)
    }
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              <div>
                <CardTitle>Scheduled Jobs</CardTitle>
                <CardDescription>Recurring collection and analysis jobs</CardDescription>
              </div>
            </div>
            <div className="flex items-center gap-3">
              {/* SSE connection indicator */}
              <div className="flex items-center gap-1.5">
                <div className={`h-2 w-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-xs text-muted-foreground">
                  {connected ? 'Live' : 'Disconnected'}
                </span>
              </div>
              <Button size="sm" onClick={openCreate}>
                <Plus className="h-4 w-4 mr-1" />
                New Job
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-3 mb-4 bg-destructive/10 text-destructive rounded-md">
              <AlertCircle className="h-4 w-4" />
              <span className="text-sm">{error}</span>
            </div>
          )}

          {/* Loading */}
          {loading && jobs.length === 0 && (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
              <span className="ml-2 text-sm text-muted-foreground">Loading jobs...</span>
            </div>
          )}

          {/* Empty state */}
          {!loading && jobs.length === 0 && (
            <div className="text-center py-8 text-sm text-muted-foreground">
              No scheduled jobs yet. Create one to automate collection and analysis.
            </div>
          )}

          {/* Job list */}
          {jobs.length > 0 && (
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.id}
                  className="flex flex-col sm:flex-row sm:items-center gap-3 p-3 border rounded-lg"
                >
                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-sm truncate">{job.name}</span>
                      <Badge variant="secondary" className="text-xs">
                        {job.platform}
                      </Badge>
                      {!job.enabled && (
                        <Badge variant="outline" className="text-xs">Paused</Badge>
                      )}
                    </div>
                    <div className="flex flex-wrap gap-1.5 mt-1">
                      {job.queries.map((q, i) => (
                        <Badge key={i} variant="outline" className="text-xs font-normal">
                          {q}
                        </Badge>
                      ))}
                    </div>
                    <div className="flex items-center gap-3 mt-1.5 text-xs text-muted-foreground">
                      <span className="font-mono">{job.cronExpression}</span>
                      <span>Next: {formatNextRun(job.nextRunAt)}</span>
                    </div>
                  </div>

                  {/* Status + Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <LastStatusBadge job={job} />

                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      title="Run now"
                      onClick={() => handleRunNow(job.id)}
                      disabled={runningJobId === job.id}
                    >
                      {runningJobId === job.id ? (
                        <Loader2 className="h-4 w-4 animate-spin" />
                      ) : (
                        <Play className="h-4 w-4" />
                      )}
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      title="History"
                      onClick={() => setHistoryJobId(historyJobId === job.id ? null : job.id)}
                    >
                      <History className="h-4 w-4" />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      title={job.enabled ? 'Pause' : 'Enable'}
                      onClick={() => handleToggleEnabled(job)}
                    >
                      <Clock className={`h-4 w-4 ${job.enabled ? 'text-green-500' : 'text-muted-foreground'}`} />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0"
                      title="Edit"
                      onClick={() => openEdit(job)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-8 w-8 p-0 text-destructive hover:text-destructive"
                      title="Delete"
                      onClick={() => handleDelete(job.id)}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}

              {/* Inline history panel */}
              {historyJobId !== null && (
                <div className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="text-sm font-medium">
                      Execution History — {jobs.find(j => j.id === historyJobId)?.name}
                    </h4>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 w-6 p-0"
                      onClick={() => setHistoryJobId(null)}
                    >
                      <X className="h-4 w-4" />
                    </Button>
                  </div>
                  <JobHistory jobId={historyJobId} />
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create / Edit Dialog */}
      <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingJob ? 'Edit Job' : 'New Scheduled Job'}</DialogTitle>
            <DialogDescription>
              {editingJob
                ? 'Update the job configuration.'
                : 'Set up a recurring collection and analysis job.'}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-2">
            {/* Name */}
            <div>
              <label className="text-sm font-medium mb-1.5 block">Job Name</label>
              <input
                type="text"
                value={formName}
                onChange={(e) => setFormName(e.target.value)}
                placeholder="e.g. Politics Monitor"
                className="w-full px-3 py-2 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
            </div>

            {/* Platform (only on create) */}
            {!editingJob && (
              <div>
                <label className="text-sm font-medium mb-1.5 block">Platform</label>
                <Select value={formPlatform} onValueChange={setFormPlatform}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {platforms.map((p) => (
                      <SelectItem key={p} value={p}>
                        {p.charAt(0).toUpperCase() + p.slice(1)}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Queries */}
            <div>
              <label className="text-sm font-medium mb-1.5 block">Search Queries</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  value={formQueryInput}
                  onChange={(e) => setFormQueryInput(e.target.value)}
                  onKeyDown={handleQueryKeyDown}
                  placeholder="#hashtag or keyword"
                  className="flex-1 px-3 py-2 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addQuery}
                  disabled={!formQueryInput.trim()}
                >
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {formQueries.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {formQueries.map((q, i) => (
                    <Badge key={i} variant="secondary" className="pl-2 pr-1 py-1 flex items-center gap-1">
                      {q}
                      <button
                        type="button"
                        onClick={() => removeQuery(q)}
                        className="ml-1 hover:bg-muted rounded-full p-0.5"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </Badge>
                  ))}
                </div>
              )}
            </div>

            {/* Cron */}
            <div>
              <label className="text-sm font-medium mb-1.5 block">Schedule (Cron)</label>
              <CronInput value={formCron} onChange={setFormCron} />
            </div>

            {/* Limit + Analysis Hours row */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-1.5 block">Posts per query</label>
                <Select value={formLimit.toString()} onValueChange={(v) => setFormLimit(parseInt(v))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {limitOptions.map((l) => (
                      <SelectItem key={l} value={l.toString()}>
                        {l.toLocaleString()}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-1.5 block">Analysis window</label>
                <Select value={formAnalysisHours.toString()} onValueChange={(v) => setFormAnalysisHours(parseInt(v))}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {analysisHoursOptions.map((h) => (
                      <SelectItem key={h} value={h.toString()}>
                        {h} {h === 1 ? 'hour' : 'hours'}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Harvest comments */}
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={formHarvestComments}
                onChange={(e) => setFormHarvestComments(e.target.checked)}
                className="rounded border-gray-300"
              />
              Harvest comments from top posts
            </label>

            {/* Form error */}
            {formError && (
              <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-md">
                <AlertCircle className="h-4 w-4" />
                <span className="text-sm">{formError}</span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSubmit} disabled={formSubmitting}>
              {formSubmitting && <Loader2 className="h-4 w-4 animate-spin mr-2" />}
              {editingJob ? 'Save Changes' : 'Create Job'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
