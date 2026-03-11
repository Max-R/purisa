/**
 * Interactive coordination score timeline chart.
 *
 * Uses recharts AreaChart with gradient fill, tooltips,
 * and a post volume bar overlay.
 */
import { useState } from 'react'
import {
  Area,
  Bar,
  ComposedChart,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Activity } from 'lucide-react'
import type { TimelineResponse } from '../types/coordination'

interface CoordinationTimelineProps {
  timeline: TimelineResponse | null
  loading: boolean
  onHoursChange?: (hours: number) => void
}

const HOUR_OPTIONS = [
  { label: '24h', value: 24 },
  { label: '48h', value: 48 },
  { label: '7d', value: 168 },
]

// Format time for X-axis labels
function formatTime(isoTime: string): string {
  const d = new Date(isoTime)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

function formatDate(isoTime: string): string {
  const d = new Date(isoTime)
  return d.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

// Custom tooltip component
function CustomTooltip({ active, payload }: { active?: boolean; payload?: any[] }) {
  if (!active || !payload || payload.length === 0) return null

  const data = payload[0]?.payload
  if (!data) return null

  const time = new Date(data.time)

  return (
    <div className="rounded-lg border bg-background p-3 shadow-md">
      <p className="font-medium text-sm mb-1.5">
        {time.toLocaleDateString()} {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </p>
      <div className="space-y-1 text-sm">
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Score:</span>
          <span className="font-mono font-medium">{data.score.toFixed(1)}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Posts:</span>
          <span className="font-mono">{data.posts}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Coordinated:</span>
          <span className="font-mono">{data.coordinated}</span>
        </div>
        <div className="flex justify-between gap-4">
          <span className="text-muted-foreground">Clusters:</span>
          <span className="font-mono">{data.clusters}</span>
        </div>
      </div>
    </div>
  )
}

export default function CoordinationTimeline({ timeline, loading, onHoursChange }: CoordinationTimelineProps) {
  const [selectedHours, setSelectedHours] = useState(168)
  const [showPosts, setShowPosts] = useState(false)

  const handleHoursChange = (hours: number) => {
    setSelectedHours(hours)
    onHoursChange?.(hours)
  }

  // Compute the data to display (filter to selected hours)
  const data = timeline?.timeline ?? []

  // Decide X-axis tick format based on hours shown
  const tickFormatter = selectedHours <= 48
    ? formatTime
    : formatDate

  // Only show every Nth tick to avoid crowding
  const tickInterval = selectedHours <= 24 ? 2 : selectedHours <= 48 ? 4 : 12

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
          <div className="flex items-center gap-2">
            <Activity className="h-5 w-5 text-muted-foreground" />
            <CardTitle className="text-lg">Coordination Timeline</CardTitle>
            {timeline && (
              <Badge variant="secondary" className="ml-1">
                {timeline.summary.dataPoints} data points
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant={showPosts ? 'default' : 'outline'}
              size="sm"
              className="text-xs h-7"
              onClick={() => setShowPosts(!showPosts)}
            >
              Posts
            </Button>
            <div className="flex gap-1">
              {HOUR_OPTIONS.map((opt) => (
                <Button
                  key={opt.value}
                  variant={selectedHours === opt.value ? 'default' : 'outline'}
                  size="sm"
                  className="text-xs h-7"
                  onClick={() => handleHoursChange(opt.value)}
                >
                  {opt.label}
                </Button>
              ))}
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {loading || !timeline ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            {loading ? 'Loading timeline...' : 'No timeline data available'}
          </div>
        ) : data.length === 0 ? (
          <div className="h-[300px] flex items-center justify-center text-muted-foreground">
            No data for the selected time range
          </div>
        ) : (
          <>
            <div className="h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={data} margin={{ top: 5, right: 10, left: 0, bottom: 5 }}>
                  <defs>
                    <linearGradient id="scoreGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="hsl(var(--destructive))" stopOpacity={0.3} />
                      <stop offset="50%" stopColor="hsl(45, 93%, 47%)" stopOpacity={0.15} />
                      <stop offset="100%" stopColor="hsl(142, 71%, 45%)" stopOpacity={0.05} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
                  <XAxis
                    dataKey="time"
                    tickFormatter={tickFormatter}
                    interval={tickInterval}
                    className="text-xs"
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                  />
                  <YAxis
                    yAxisId="score"
                    domain={[0, 'auto']}
                    className="text-xs"
                    tick={{ fill: 'hsl(var(--muted-foreground))' }}
                    width={40}
                  />
                  {showPosts && (
                    <YAxis
                      yAxisId="posts"
                      orientation="right"
                      className="text-xs"
                      tick={{ fill: 'hsl(var(--muted-foreground))' }}
                      width={40}
                    />
                  )}
                  <Tooltip content={<CustomTooltip />} />
                  <Area
                    yAxisId="score"
                    type="monotone"
                    dataKey="score"
                    stroke="hsl(var(--primary))"
                    strokeWidth={2}
                    fill="url(#scoreGradient)"
                    dot={false}
                    activeDot={{ r: 4, fill: 'hsl(var(--primary))' }}
                  />
                  {showPosts && (
                    <Bar
                      yAxisId="posts"
                      dataKey="posts"
                      fill="hsl(var(--muted-foreground))"
                      opacity={0.2}
                      radius={[2, 2, 0, 0]}
                    />
                  )}
                </ComposedChart>
              </ResponsiveContainer>
            </div>

            {/* Summary row */}
            <div className="flex flex-wrap gap-4 mt-3 pt-3 border-t text-sm text-muted-foreground">
              <span>
                Avg: <span className="font-mono font-medium text-foreground">{timeline.summary.averageScore.toFixed(1)}</span>
              </span>
              <span>
                Peak: <span className="font-mono font-medium text-foreground">{timeline.summary.peakScore.toFixed(1)}</span>
              </span>
              <span>
                Posts: <span className="font-mono font-medium text-foreground">{timeline.summary.totalPostsAnalyzed.toLocaleString()}</span>
              </span>
              <span>
                Coordinated: <span className="font-mono font-medium text-foreground">{timeline.summary.totalCoordinated.toLocaleString()}</span>
              </span>
            </div>
          </>
        )}
      </CardContent>
    </Card>
  )
}
