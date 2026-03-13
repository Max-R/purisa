/**
 * Clusters table showing detected coordination clusters.
 *
 * Rows are expandable to show coordination pattern evidence.
 * No individual account identifiers are exposed — only aggregate
 * pattern data (timing, shared URLs, text similarity, etc.).
 */
import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Network, ChevronDown, ChevronRight, Timer, Link, FileText, Hash, MessageSquareReply } from 'lucide-react'
import InfoTooltip from './InfoTooltip'
import type { ClustersResponse, Cluster, ClusterPatterns } from '../types/coordination'

interface ClustersTableProps {
  clusters: ClustersResponse | null
  loading: boolean
}

function scoreColor(score: number): 'destructive' | 'warning' | 'secondary' {
  if (score >= 60) return 'destructive'
  if (score >= 30) return 'warning'
  return 'secondary'
}

// Readable cluster type labels + descriptions
const CLUSTER_TYPES: Record<string, { label: string; description: string }> = {
  sync_posting: { label: 'Sync Posting', description: 'Accounts posting within 90 seconds of each other' },
  url: { label: 'URL Sharing', description: 'Accounts sharing the same URLs in a short window' },
  text: { label: 'Similar Text', description: 'Accounts posting near-identical text content (TF-IDF similarity > 0.8)' },
  hashtag: { label: 'Hashtag Overlap', description: 'Accounts using the same uncommon hashtag combinations' },
  reply_pattern: { label: 'Reply Pattern', description: 'Accounts replying to the same targets in a coordinated pattern' },
  mixed: { label: 'Mixed Signals', description: 'Multiple coordination signals detected (e.g. timing + content)' },
}

// Colors for edge type distribution bar
const EDGE_TYPE_COLORS: Record<string, string> = {
  synchronized_posting: 'bg-blue-500',
  url_sharing: 'bg-purple-500',
  text_similarity: 'bg-amber-500',
  hashtag: 'bg-green-500',
  reply_pattern: 'bg-rose-500',
}

const EDGE_TYPE_LABELS: Record<string, string> = {
  synchronized_posting: 'Sync Posting',
  url_sharing: 'URL Sharing',
  text_similarity: 'Text Similarity',
  hashtag: 'Hashtag Overlap',
  reply_pattern: 'Reply Pattern',
}

function getClusterType(type: string | null): { label: string; description: string } {
  if (!type) return CLUSTER_TYPES.mixed
  return CLUSTER_TYPES[type] ?? { label: type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()), description: 'Coordination pattern detected' }
}

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.toLocaleDateString([], { month: 'short', day: 'numeric' })} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

function EdgeDistributionBar({ distribution }: { distribution: Record<string, number> }) {
  const total = Object.values(distribution).reduce((s, v) => s + v, 0)
  if (total === 0) return null

  return (
    <div className="space-y-1.5">
      <div className="flex h-2.5 rounded-full overflow-hidden bg-muted">
        {Object.entries(distribution).map(([type, count]) => (
          <div
            key={type}
            className={`${EDGE_TYPE_COLORS[type] ?? 'bg-gray-400'} transition-all`}
            style={{ width: `${(count / total) * 100}%` }}
            title={`${EDGE_TYPE_LABELS[type] ?? type}: ${count} connections`}
          />
        ))}
      </div>
      <div className="flex flex-wrap gap-3 text-xs text-muted-foreground">
        {Object.entries(distribution).map(([type, count]) => (
          <span key={type} className="flex items-center gap-1">
            <span className={`inline-block h-2 w-2 rounded-full ${EDGE_TYPE_COLORS[type] ?? 'bg-gray-400'}`} />
            {EDGE_TYPE_LABELS[type] ?? type} ({count})
          </span>
        ))}
      </div>
    </div>
  )
}

function PatternDetails({ patterns, memberCount, edgeCount, density }: {
  patterns: ClusterPatterns
  memberCount: number
  edgeCount: number
  density: number
}) {
  return (
    <div className="space-y-3">
      {/* Edge type distribution bar */}
      <EdgeDistributionBar distribution={patterns.edgeTypeDistribution} />

      {/* Pattern-specific detail sections */}
      <div className="space-y-2">
        {patterns.syncPosting && (
          <div className="flex items-start gap-2 text-sm">
            <Timer className="h-4 w-4 text-blue-500 mt-0.5 shrink-0" />
            <div>
              <span className="font-medium">{patterns.syncPosting.count} pairs</span> posted within seconds of each other
              <span className="text-muted-foreground">
                {' '}&mdash; avg gap: {patterns.syncPosting.avgTimeDiffSeconds}s, fastest: {patterns.syncPosting.minTimeDiffSeconds}s
              </span>
            </div>
          </div>
        )}

        {patterns.urlSharing && (
          <div className="flex items-start gap-2 text-sm">
            <Link className="h-4 w-4 text-purple-500 mt-0.5 shrink-0" />
            <div>
              <span className="font-medium">{patterns.urlSharing.count} pairs</span> shared the same URLs
              {patterns.urlSharing.sharedUrls.length > 0 && (
                <div className="mt-1 space-y-0.5">
                  {patterns.urlSharing.sharedUrls.map((url, i) => (
                    <div key={i} className="text-xs text-muted-foreground font-mono truncate max-w-md" title={url}>
                      {url}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {patterns.textSimilarity && (
          <div className="flex items-start gap-2 text-sm">
            <FileText className="h-4 w-4 text-amber-500 mt-0.5 shrink-0" />
            <div>
              <span className="font-medium">{patterns.textSimilarity.count} pairs</span> posted near-identical text
              <span className="text-muted-foreground">
                {' '}(avg {Math.round(patterns.textSimilarity.avgSimilarity * 100)}% match)
              </span>
              {patterns.textSimilarity.sampleSnippets.length > 0 && (
                <div className="mt-1.5 space-y-1">
                  {patterns.textSimilarity.sampleSnippets.map((snippet, i) => (
                    <blockquote
                      key={i}
                      className="border-l-2 border-amber-300 dark:border-amber-700 pl-2.5 text-xs text-muted-foreground italic"
                    >
                      &ldquo;{snippet.text}&rdquo;
                      <span className="not-italic ml-1.5 text-amber-600 dark:text-amber-400">
                        ({Math.round(snippet.similarity * 100)}%)
                      </span>
                    </blockquote>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {patterns.hashtagOverlap && (
          <div className="flex items-start gap-2 text-sm">
            <Hash className="h-4 w-4 text-green-500 mt-0.5 shrink-0" />
            <div>
              <span className="font-medium">{patterns.hashtagOverlap.count} pairs</span> used the same hashtags
              {patterns.hashtagOverlap.sharedHashtags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-1">
                  {patterns.hashtagOverlap.sharedHashtags.map((tag) => (
                    <Badge key={tag} variant="outline" className="text-xs py-0 h-5">
                      #{tag}
                    </Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {patterns.replyPattern && (
          <div className="flex items-start gap-2 text-sm">
            <MessageSquareReply className="h-4 w-4 text-rose-500 mt-0.5 shrink-0" />
            <div>
              <span className="font-medium">{patterns.replyPattern.count} pairs</span> replied to the same targets
            </div>
          </div>
        )}
      </div>

      {/* Network summary */}
      <div className="text-xs text-muted-foreground pt-1 border-t">
        {memberCount} accounts &middot; {edgeCount} connections &middot; density {density.toFixed(2)}
      </div>
    </div>
  )
}

function ClusterRow({ cluster }: { cluster: Cluster }) {
  const [expanded, setExpanded] = useState(false)
  const hasPatterns = Object.keys(cluster.patterns.edgeTypeDistribution).length > 0

  return (
    <>
      <TableRow
        className="cursor-pointer hover:bg-muted/50"
        onClick={() => setExpanded(!expanded)}
      >
        <TableCell className="w-8">
          <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
            {expanded
              ? <ChevronDown className="h-3.5 w-3.5" />
              : <ChevronRight className="h-3.5 w-3.5" />
            }
          </Button>
        </TableCell>
        <TableCell className="font-mono text-xs">
          {formatTime(cluster.detectedAt)}
        </TableCell>
        <TableCell className="text-center font-medium">
          {cluster.memberCount}
        </TableCell>
        <TableCell className="text-center text-muted-foreground text-xs">
          {cluster.edgeCount}
        </TableCell>
        <TableCell className="text-center">
          {cluster.density.toFixed(2)}
        </TableCell>
        <TableCell className="text-center">
          <Badge variant={scoreColor(cluster.coordinationScore)}>
            {cluster.coordinationScore.toFixed(1)}
          </Badge>
        </TableCell>
        <TableCell>
          {(() => {
            const ct = getClusterType(cluster.clusterType)
            return (
              <Badge variant="outline" className="text-xs" title={ct.description}>
                {ct.label}
              </Badge>
            )
          })()}
        </TableCell>
      </TableRow>

      {expanded && hasPatterns && (
        <TableRow>
          <TableCell colSpan={7} className="bg-muted/30 py-3 px-8">
            <PatternDetails
              patterns={cluster.patterns}
              memberCount={cluster.memberCount}
              edgeCount={cluster.edgeCount}
              density={cluster.density}
            />
          </TableCell>
        </TableRow>
      )}
    </>
  )
}

export default function ClustersTable({ clusters, loading }: ClustersTableProps) {
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Network className="h-5 w-5 text-muted-foreground" />
            Detected Clusters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-32 flex items-center justify-center text-muted-foreground">
            Loading clusters...
          </div>
        </CardContent>
      </Card>
    )
  }

  const clusterList = clusters?.clusters ?? []

  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CardTitle className="text-lg flex items-center gap-2">
              <Network className="h-5 w-5 text-muted-foreground" />
              Detected Clusters
            </CardTitle>
            <InfoTooltip text="Groups of 3+ accounts that show coordinated behavior patterns. Click a row to see what coordination patterns were detected and the supporting evidence." />
          </div>
          <Badge variant="secondary">
            {clusterList.length} {clusterList.length === 1 ? 'cluster' : 'clusters'}
          </Badge>
        </div>
        {clusterList.length > 0 && (
          <div className="flex flex-wrap gap-3 text-xs text-muted-foreground mt-1">
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 rounded-full bg-red-500" />
              60+ High
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 rounded-full bg-yellow-500" />
              30–59 Moderate
            </span>
            <span className="flex items-center gap-1.5">
              <span className="inline-block h-2 w-2 rounded-full bg-gray-400" />
              &lt;30 Low
            </span>
          </div>
        )}
      </CardHeader>

      <CardContent className="p-0">
        {clusterList.length === 0 ? (
          <div className="py-12 text-center text-muted-foreground">
            <Network className="h-10 w-10 mx-auto mb-3 opacity-50" />
            <p>No clusters detected in the last 24 hours</p>
            <p className="text-sm mt-1">Run a coordination analysis to detect clusters</p>
          </div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-8" />
                <TableHead title="When this cluster was first detected">Detected</TableHead>
                <TableHead className="text-center" title="Number of accounts in this coordination cluster">Accounts</TableHead>
                <TableHead className="text-center" title="Number of coordination connections (edges) between cluster members">Evidence</TableHead>
                <TableHead className="text-center" title="Network density (0-1). Higher values mean more connections between cluster members.">Density</TableHead>
                <TableHead className="text-center" title="Coordination score (0-100). Higher = stronger coordination signals.">Score</TableHead>
                <TableHead title="Primary coordination pattern that formed this cluster">Type</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {clusterList.map((cluster) => (
                <ClusterRow key={cluster.clusterId} cluster={cluster} />
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  )
}
