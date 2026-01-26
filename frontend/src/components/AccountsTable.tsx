import { useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { AlertCircle, Users, Loader2, MessageSquare, Flame, Eye, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import type { AccountWithScore } from '../types/account'
import { apiClient, AccountComment } from '../api/client'

interface AccountsTableProps {
  accounts: AccountWithScore[]
  loading: boolean
  error: string | null
  showCommentStats?: boolean
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

function CommentStatsDisplay({
  stats,
  onViewComments
}: {
  stats: AccountWithScore['commentStats']
  onViewComments?: () => void
}) {
  if (!stats) {
    return <span className="text-xs text-muted-foreground italic">—</span>
  }

  const hasInflammatory = stats.inflammatoryCount > 0
  const highRatio = stats.inflammatoryRatio > 0.1

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm">{stats.totalComments}</span>
      {hasInflammatory && (
        <Badge
          variant={highRatio ? "destructive" : "warning"}
          className="text-xs flex items-center gap-1"
        >
          <Flame className="h-3 w-3" />
          {stats.inflammatoryCount}
        </Badge>
      )}
      {stats.totalComments > 0 && onViewComments && (
        <Button
          variant="ghost"
          size="sm"
          className="h-6 px-2 text-xs"
          onClick={onViewComments}
        >
          <Eye className="h-3 w-3 mr-1" />
          View
        </Button>
      )}
    </div>
  )
}

interface CommentsDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  account: AccountWithScore | null
}

function CommentsDialog({ open, onOpenChange, account }: CommentsDialogProps) {
  const [comments, setComments] = useState<AccountComment[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [totalComments, setTotalComments] = useState(0)

  const loadComments = async () => {
    if (!account) return

    setLoading(true)
    setError(null)
    try {
      const result = await apiClient.getAccountComments(
        account.account.platform,
        account.account.id,
        100,
        0,
        true
      )
      setComments(result.comments)
      setTotalComments(result.totalComments)
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load comments')
    } finally {
      setLoading(false)
    }
  }

  // Load comments when dialog opens
  if (open && comments.length === 0 && !loading && !error && account) {
    loadComments()
  }

  // Reset when dialog closes
  const handleOpenChange = (newOpen: boolean) => {
    if (!newOpen) {
      setComments([])
      setError(null)
    }
    onOpenChange(newOpen)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-3xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Comments by @{account?.account.username}
            {totalComments > 0 && (
              <Badge variant="secondary" className="ml-2">
                {totalComments} total
              </Badge>
            )}
          </DialogTitle>
        </DialogHeader>

        {loading && (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            <span className="ml-2 text-sm text-muted-foreground">Loading comments...</span>
          </div>
        )}

        {error && (
          <div className="text-center py-8">
            <AlertCircle className="h-8 w-8 mx-auto text-destructive mb-2" />
            <p className="text-sm text-muted-foreground">{error}</p>
          </div>
        )}

        {!loading && !error && comments.length === 0 && (
          <div className="text-center py-8">
            <MessageSquare className="h-8 w-8 mx-auto text-muted-foreground mb-2" />
            <p className="text-sm text-muted-foreground">No comments found</p>
          </div>
        )}

        {!loading && !error && comments.length > 0 && (
          <ScrollArea className="h-[60vh] pr-4">
            <div className="space-y-4">
              {comments.map((comment) => (
                <div
                  key={comment.id}
                  className={cn(
                    "p-4 rounded-lg border",
                    comment.inflammatory && "border-destructive/50 bg-destructive/5"
                  )}
                >
                  {/* Parent post context */}
                  {comment.parentPreview && (
                    <div className="mb-2 pl-3 border-l-2 border-muted text-xs text-muted-foreground">
                      <span className="font-medium">Replying to:</span>{' '}
                      {comment.parentPreview.contentSnippet
                        ? comment.parentPreview.contentSnippet.slice(0, 100) + '...'
                        : 'Original post'}
                    </div>
                  )}

                  {/* Comment content */}
                  <p className="text-sm whitespace-pre-wrap">{comment.content}</p>

                  {/* Metadata row */}
                  <div className="mt-3 flex items-center gap-3 text-xs text-muted-foreground">
                    {comment.createdAt && (
                      <span>
                        {new Date(comment.createdAt).toLocaleString()}
                      </span>
                    )}
                    {comment.engagement && Object.keys(comment.engagement).length > 0 && (
                      <span>
                        {Object.entries(comment.engagement)
                          .filter(([_, v]) => v > 0)
                          .map(([k, v]) => `${v} ${k}`)
                          .join(', ')}
                      </span>
                    )}
                  </div>

                  {/* Inflammatory badge */}
                  {comment.inflammatory && (
                    <div className="mt-2 flex items-center gap-2">
                      <Badge variant="destructive" className="text-xs">
                        <Flame className="h-3 w-3 mr-1" />
                        Inflammatory (severity: {comment.inflammatory.severityScore.toFixed(2)})
                      </Badge>
                      {comment.inflammatory.triggeredCategories.map((cat) => (
                        <Badge key={cat} variant="outline" className="text-xs">
                          {cat}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </ScrollArea>
        )}
      </DialogContent>
    </Dialog>
  )
}

export default function AccountsTable({ accounts, loading, error, showCommentStats = false }: AccountsTableProps) {
  const [selectedAccount, setSelectedAccount] = useState<AccountWithScore | null>(null)
  const [commentsDialogOpen, setCommentsDialogOpen] = useState(false)

  const handleViewComments = (account: AccountWithScore) => {
    setSelectedAccount(account)
    setCommentsDialogOpen(true)
  }

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
              {showCommentStats && <TableHead>Comments</TableHead>}
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

                {showCommentStats && (
                  <TableCell>
                    <CommentStatsDisplay
                      stats={item.commentStats}
                      onViewComments={() => handleViewComments(item)}
                    />
                  </TableCell>
                )}

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
              {showCommentStats && item.commentStats && item.commentStats.totalComments > 0 && (
                <Button
                  variant="outline"
                  size="sm"
                  className="h-6 text-xs"
                  onClick={() => handleViewComments(item)}
                >
                  <Eye className="h-3 w-3 mr-1" />
                  {item.commentStats.totalComments} comments
                </Button>
              )}
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

      {/* Comments Dialog */}
      <CommentsDialog
        open={commentsDialogOpen}
        onOpenChange={setCommentsDialogOpen}
        account={selectedAccount}
      />
    </>
  )
}
