import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, Users, Loader2, MessageSquare } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AccountWithScore } from '../types/account'

interface AccountsTableProps {
  accounts: AccountWithScore[]
  loading: boolean
  error: string | null
}

function getScoreVariant(score: number): "destructive" | "warning" | "success" {
  if (score >= 8) return "destructive"
  if (score >= 7) return "warning"
  return "success"
}

function getScoreLabel(score: number): string {
  if (score >= 8) return 'High'
  if (score >= 7) return 'Medium'
  return 'Low'
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric'
  })
}

function ScoreDisplay({ score }: { score: number }) {
  const variant = getScoreVariant(score)
  return (
    <div className="flex items-center gap-2">
      <span className={cn(
        "text-lg font-bold",
        variant === "destructive" && "text-destructive",
        variant === "warning" && "text-yellow-600",
        variant === "success" && "text-green-600"
      )}>
        {score.toFixed(1)}
      </span>
      <Badge variant={variant} className="text-xs">
        {getScoreLabel(score)}
      </Badge>
    </div>
  )
}

export default function AccountsTable({ accounts, loading, error }: AccountsTableProps) {
  if (loading) {
    return (
      <div className="p-8 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        <span className="ml-2 text-sm text-muted-foreground">Loading accounts...</span>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-8 text-center">
        <AlertCircle className="h-12 w-12 mx-auto text-destructive mb-4" />
        <p className="font-medium">Failed to load accounts</p>
        <p className="text-sm text-muted-foreground mt-1">{error}</p>
      </div>
    )
  }

  if (accounts.length === 0) {
    return (
      <div className="p-8 text-center">
        <Users className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
        <p className="text-muted-foreground">No accounts found</p>
      </div>
    )
  }

  return (
    <>
      {/* Desktop Table View */}
      <div className="hidden md:block">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Account</TableHead>
              <TableHead>Platform</TableHead>
              <TableHead>Score</TableHead>
              <TableHead>Activity</TableHead>
              <TableHead>Top Signals</TableHead>
              <TableHead>Created</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {accounts.map((item) => (
              <TableRow key={item.account.id}>
                <TableCell>
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-full bg-muted flex items-center justify-center">
                      <span className="text-sm font-medium">
                        {(item.account.displayName || item.account.username).charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="font-medium">
                        {item.account.displayName || item.account.username}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        @{item.account.username}
                      </p>
                    </div>
                  </div>
                </TableCell>

                <TableCell>
                  <Badge variant="secondary" className="capitalize">
                    {item.account.platform}
                  </Badge>
                </TableCell>

                <TableCell>
                  <ScoreDisplay score={item.score.totalScore} />
                </TableCell>

                <TableCell>
                  <div className="text-sm text-muted-foreground space-y-1">
                    <div className="flex items-center gap-1.5">
                      <MessageSquare className="h-3.5 w-3.5" />
                      <span>{item.account.postCount.toLocaleString()} posts</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Users className="h-3.5 w-3.5" />
                      <span>{item.account.followerCount.toLocaleString()} followers</span>
                    </div>
                  </div>
                </TableCell>

                <TableCell>
                  <div className="flex flex-wrap gap-1 max-w-[200px]">
                    {Object.entries(item.score.signals)
                      .sort((a, b) => b[1] - a[1])
                      .slice(0, 3)
                      .filter(([_, v]) => v > 0)
                      .map(([signal, value]) => (
                        <Badge
                          key={signal}
                          variant={value >= 2 ? "destructive" : value >= 1 ? "warning" : "outline"}
                          className="text-xs"
                        >
                          {signal.replace(/_/g, ' ')}
                        </Badge>
                      ))}
                    {Object.entries(item.score.signals).filter(([_, v]) => v > 0).length === 0 && (
                      <span className="text-xs text-muted-foreground italic">None</span>
                    )}
                  </div>
                </TableCell>

                <TableCell className="text-muted-foreground">
                  {item.account.createdAt ? formatDate(item.account.createdAt) : '—'}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden divide-y">
        {accounts.map((item) => (
          <div key={item.account.id} className="p-4">
            <div className="flex items-start justify-between gap-3 mb-3">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-full bg-muted flex items-center justify-center">
                  <span className="text-sm font-medium">
                    {(item.account.displayName || item.account.username).charAt(0).toUpperCase()}
                  </span>
                </div>
                <div>
                  <p className="font-medium">
                    {item.account.displayName || item.account.username}
                  </p>
                  <p className="text-sm text-muted-foreground">@{item.account.username}</p>
                </div>
              </div>
              <ScoreDisplay score={item.score.totalScore} />
            </div>

            <div className="flex flex-wrap items-center gap-2 mb-3">
              <Badge variant="secondary" className="capitalize">
                {item.account.platform}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {item.account.postCount.toLocaleString()} posts
              </span>
              <span className="text-xs text-muted-foreground">
                {item.account.followerCount.toLocaleString()} followers
              </span>
            </div>

            <div className="flex flex-wrap gap-1">
              {Object.entries(item.score.signals)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 4)
                .filter(([_, v]) => v > 0)
                .map(([signal, value]) => (
                  <Badge
                    key={signal}
                    variant={value >= 2 ? "destructive" : value >= 1 ? "warning" : "outline"}
                    className="text-xs"
                  >
                    {signal.replace(/_/g, ' ')}
                  </Badge>
                ))}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
