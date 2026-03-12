/**
 * Data context banner — tells the user what data is being visualized.
 *
 * Shows which scheduled jobs and manual queries have contributed data to
 * the current dashboard view, and provides a dropdown to filter by query.
 */
import { Card, CardContent } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { BarChart3, Clock, Calendar } from 'lucide-react'
import InfoTooltip from './InfoTooltip'
import type { QueriesResponse } from '../types/coordination'
import type { ScheduledJob } from '../types/schedule'

interface DataContextBannerProps {
  platform: string
  queries: QueriesResponse | null
  jobs: ScheduledJob[]
  selectedQuery: string | null
  onQueryChange: (query: string | null) => void
}

function formatRelativeTime(isoString: string | null): string {
  if (!isoString) return 'never'
  try {
    const date = new Date(isoString)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMin = Math.floor(diffMs / 60000)
    if (diffMin < 1) return 'just now'
    if (diffMin < 60) return `${diffMin}m ago`
    const diffHrs = Math.floor(diffMin / 60)
    if (diffHrs < 24) return `${diffHrs}h ago`
    const diffDays = Math.floor(diffHrs / 24)
    return `${diffDays}d ago`
  } catch {
    return isoString
  }
}

function formatDate(isoString: string | null): string {
  if (!isoString) return ''
  try {
    return new Date(isoString).toLocaleDateString(undefined, {
      month: 'short',
      day: 'numeric',
    })
  } catch {
    return ''
  }
}

export default function DataContextBanner({
  platform,
  queries,
  jobs,
  selectedQuery,
  onQueryChange,
}: DataContextBannerProps) {
  const platformJobs = jobs.filter(
    (j) => j.platform === platform && j.enabled
  )
  const queryList = queries?.queries ?? []
  const totalPosts = queryList.reduce((sum, q) => sum + q.postCount, 0)

  // Nothing to show yet
  if (queryList.length === 0 && platformJobs.length === 0) {
    return null
  }

  // Build the filter options: "All queries" + each distinct query
  const filterOptions = queryList
    .filter((q) => q.query !== '(unknown)')
    .sort((a, b) => b.postCount - a.postCount)

  return (
    <Card className="border-muted">
      <CardContent className="py-3 px-4">
        <div className="flex flex-col gap-3">
          {/* Header row */}
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4 text-muted-foreground shrink-0" />
              <span className="text-sm font-medium">
                Showing: {platform.charAt(0).toUpperCase() + platform.slice(1)} coordination data
              </span>
              <InfoTooltip
                text="The visualizations below reflect data collected from the listed sources. Use the query filter to focus on a specific search term."
                side="bottom"
              />
              {totalPosts > 0 && (
                <Badge variant="secondary" className="text-xs">
                  {totalPosts.toLocaleString()} posts
                </Badge>
              )}
            </div>

            {/* Query filter dropdown */}
            {filterOptions.length > 0 && (
              <Select
                value={selectedQuery ?? '__all__'}
                onValueChange={(v) => onQueryChange(v === '__all__' ? null : v)}
              >
                <SelectTrigger className="w-[200px] h-8 text-xs">
                  <SelectValue placeholder="All queries" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__all__">All queries</SelectItem>
                  {filterOptions.map((q) => (
                    <SelectItem key={q.query} value={q.query}>
                      {q.query} ({q.postCount.toLocaleString()})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          </div>

          {/* Sources list */}
          <div className="flex flex-col gap-1.5 text-sm text-muted-foreground">
            {/* Scheduled jobs */}
            {platformJobs.map((job) => (
              <div key={job.id} className="flex items-center gap-2 pl-6 flex-wrap">
                <Clock className="h-3.5 w-3.5 shrink-0" />
                <span className="font-medium text-foreground">{job.name}</span>
                <span className="text-xs">
                  — {job.queries.join(', ')}
                </span>
                <span className="text-xs text-muted-foreground">
                  ({job.cronExpression}
                  {job.lastExecution && (
                    <>, last run {formatRelativeTime(job.lastExecution.startedAt)}</>
                  )}
                  )
                </span>
              </div>
            ))}

            {/* Manual / distinct queries not from jobs */}
            {queryList
              .filter((q) => {
                // Show queries that aren't obviously from scheduled jobs
                const jobQueries = platformJobs.flatMap((j) => j.queries)
                return !jobQueries.includes(q.query) && q.query !== '(unknown)'
              })
              .map((q) => (
                <div key={q.query} className="flex items-center gap-2 pl-6 flex-wrap">
                  <Calendar className="h-3.5 w-3.5 shrink-0" />
                  <span className="text-xs">
                    Manual — <span className="font-medium text-foreground">{q.query}</span>
                  </span>
                  <Badge variant="outline" className="text-xs py-0 h-5">
                    {q.postCount.toLocaleString()} posts
                  </Badge>
                  {q.latest && (
                    <span className="text-xs">{formatDate(q.latest)}</span>
                  )}
                </div>
              ))}

            {/* Legacy data (no source_query) */}
            {queryList
              .filter((q) => q.query === '(unknown)')
              .map((q) => (
                <div key="unknown" className="flex items-center gap-2 pl-6 flex-wrap">
                  <Calendar className="h-3.5 w-3.5 shrink-0 opacity-50" />
                  <span className="text-xs italic">
                    Pre-tracking data
                  </span>
                  <Badge variant="outline" className="text-xs py-0 h-5">
                    {q.postCount.toLocaleString()} posts
                  </Badge>
                </div>
              ))}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
