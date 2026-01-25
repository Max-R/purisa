import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { Users, MessageSquare, AlertTriangle, BarChart3, MessageCircle, Flame, Zap } from "lucide-react"
import type { Stats, CommentStats } from '../types/detection'

interface StatsCardsProps {
  stats: Stats | null
  commentStats: CommentStats | null
  loading: boolean
}

interface StatCardProps {
  label: string
  value: string | number
  icon: React.ReactNode
  description?: string
}

function StatCard({ label, value, icon, description }: StatCardProps) {
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-muted-foreground">{label}</p>
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

export default function StatsCards({ stats, commentStats, loading }: StatsCardsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 7 }).map((_, i) => (
          <StatCardSkeleton key={i} />
        ))}
      </div>
    )
  }

  if (!stats) {
    return (
      <Card className="p-12 text-center">
        <BarChart3 className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No statistics available</p>
      </Card>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Total Accounts"
        value={stats.totalAccounts}
        icon={<Users className="h-5 w-5 text-muted-foreground" />}
        description="Monitored accounts"
      />

      <StatCard
        label="Total Posts"
        value={stats.totalPosts}
        icon={<MessageSquare className="h-5 w-5 text-muted-foreground" />}
        description="Collected for analysis"
      />

      <StatCard
        label="Flagged"
        value={stats.flaggedAccounts}
        icon={<AlertTriangle className="h-5 w-5 text-destructive" />}
        description="Exceeding threshold"
      />

      <StatCard
        label="Flag Rate"
        value={`${(stats.flagRate * 100).toFixed(1)}%`}
        icon={<BarChart3 className="h-5 w-5 text-muted-foreground" />}
        description="Of all accounts"
      />

      {commentStats && (
        <>
          <StatCard
            label="Comments"
            value={commentStats.totalCommentsCollected}
            icon={<MessageCircle className="h-5 w-5 text-muted-foreground" />}
            description="Total analyzed"
          />

          <StatCard
            label="Inflammatory"
            value={commentStats.inflammatoryFlags}
            icon={<Flame className="h-5 w-5 text-destructive" />}
            description="Toxic content"
          />

          <StatCard
            label="Avg Severity"
            value={`${(commentStats.avgSeverity * 100).toFixed(0)}%`}
            icon={<Zap className="h-5 w-5 text-muted-foreground" />}
            description="Toxicity level"
          />
        </>
      )}
    </div>
  )
}
