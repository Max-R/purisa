/**
 * Stat cards for coordination detection metrics.
 *
 * Replaces the legacy StatsCards (account-based bot scoring)
 * with coordination-focused stats.
 */
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Activity, TrendingUp, Network, FileText, BarChart3 } from 'lucide-react'
import InfoTooltip from './InfoTooltip'
import type { CoordinationStats } from '../types/coordination'

interface CoordinationStatsCardsProps {
  stats: CoordinationStats | null
  loading: boolean
}

interface StatCardProps {
  label: string
  value: string | number
  icon: React.ReactNode
  description?: string
  tooltip?: string
}

function StatCard({ label, value, icon, description, tooltip }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground flex items-center gap-1">
              {label}
              {tooltip && <InfoTooltip text={tooltip} />}
            </p>
            <p className="text-2xl font-bold mt-1">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
            {description && (
              <p className="text-xs text-muted-foreground mt-1">{description}</p>
            )}
          </div>
          <div className="h-10 w-10 rounded-lg bg-muted flex items-center justify-center">
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function StatCardSkeleton() {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-16" />
          </div>
          <Skeleton className="h-10 w-10 rounded-lg" />
        </div>
      </CardContent>
    </Card>
  )
}

export default function CoordinationStatsCards({ stats, loading }: CoordinationStatsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {Array.from({ length: 5 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!stats) {
    return (
      <Card className="p-12 text-center">
        <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No coordination data available</p>
        <p className="text-sm text-muted-foreground mt-1">Run a collection + analysis job to generate data</p>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
      <StatCard
        label="Posts Analyzed"
        value={stats.last24h.totalPosts}
        icon={<FileText className="h-5 w-5 text-muted-foreground" />}
        description="Last 24 hours"
        tooltip="Total posts collected and analyzed for coordination patterns in the last 24 hours."
      />

      <StatCard
        label="Peak Score"
        value={stats.last24h.peakScore.toFixed(1)}
        icon={<TrendingUp className="h-5 w-5 text-destructive" />}
        description="24h max coordination"
        tooltip="Highest coordination score (0-100) in a single hour. Scores above 60 indicate high coordination."
      />

      <StatCard
        label="Clusters (24h)"
        value={stats.totalClustersDetected}
        icon={<Network className="h-5 w-5 text-muted-foreground" />}
        description="Groups detected"
        tooltip="Groups of 3+ accounts acting in coordinated patterns. More clusters may indicate organized campaigns."
      />

      <StatCard
        label="Coordinated"
        value={stats.last24h.totalCoordinated}
        icon={<Activity className="h-5 w-5 text-muted-foreground" />}
        description="Posts in clusters"
        tooltip="Posts attributed to accounts within detected coordination clusters."
      />

      <StatCard
        label="Avg Score (7d)"
        value={stats.last7d.avgScore.toFixed(1)}
        icon={<BarChart3 className="h-5 w-5 text-muted-foreground" />}
        description="Weekly average"
        tooltip="Average hourly coordination score over 7 days. Useful as a baseline to compare against daily peaks."
      />
    </div>
  )
}
