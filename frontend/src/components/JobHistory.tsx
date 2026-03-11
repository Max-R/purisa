/**
 * Execution history table for a scheduled job.
 */
import { useState, useEffect } from 'react'
import { Badge } from '@/components/ui/badge'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Loader2 } from 'lucide-react'
import type { JobExecution } from '../types/schedule'
import { apiClient } from '../api/client'

interface JobHistoryProps {
  jobId: number
}

function StatusBadge({ status }: { status: JobExecution['status'] }) {
  switch (status) {
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
    case 'pending':
      return <Badge variant="secondary">Pending</Badge>
    default:
      return <Badge variant="secondary">{status}</Badge>
  }
}

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '-'
  if (seconds < 1) return '<1s'
  if (seconds < 60) return `${Math.round(seconds)}s`
  const mins = Math.floor(seconds / 60)
  const secs = Math.round(seconds % 60)
  return `${mins}m ${secs}s`
}

function formatTime(isoString: string | null): string {
  if (!isoString) return '-'
  try {
    const date = new Date(isoString)
    return date.toLocaleString(undefined, {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return isoString
  }
}

export default function JobHistory({ jobId }: JobHistoryProps) {
  const [executions, setExecutions] = useState<JobExecution[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    let cancelled = false

    async function load() {
      setLoading(true)
      try {
        const result = await apiClient.getJobHistory(jobId, 20, 0)
        if (!cancelled) {
          setExecutions(result.executions)
          setTotal(result.total)
        }
      } catch (e) {
        console.error('Failed to load job history:', e)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => { cancelled = true }
  }, [jobId])

  if (loading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="h-5 w-5 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading history...</span>
      </div>
    )
  }

  if (executions.length === 0) {
    return (
      <div className="text-center py-8 text-sm text-muted-foreground">
        No executions yet. Click "Run Now" to start the first run.
      </div>
    )
  }

  return (
    <div>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Started</TableHead>
            <TableHead>Duration</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="text-right">Posts</TableHead>
            <TableHead className="text-right">Score</TableHead>
            <TableHead className="text-right">Clusters</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {executions.map((exec) => (
            <TableRow key={exec.id}>
              <TableCell className="text-sm">{formatTime(exec.startedAt)}</TableCell>
              <TableCell className="text-sm">{formatDuration(exec.durationSeconds)}</TableCell>
              <TableCell>
                <StatusBadge status={exec.status} />
              </TableCell>
              <TableCell className="text-right text-sm">{exec.postsCollected}</TableCell>
              <TableCell className="text-right text-sm">
                {exec.coordinationScore !== null ? exec.coordinationScore.toFixed(1) : '-'}
              </TableCell>
              <TableCell className="text-right text-sm">{exec.clustersDetected}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
      {total > 20 && (
        <div className="text-xs text-muted-foreground text-center py-2">
          Showing 20 of {total} executions
        </div>
      )}
    </div>
  )
}
