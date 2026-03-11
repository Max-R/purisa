/**
 * Clusters table showing detected coordination clusters.
 *
 * Rows are expandable to show cluster members.
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
import { Network, ChevronDown, ChevronRight } from 'lucide-react'
import type { ClustersResponse, Cluster } from '../types/coordination'

interface ClustersTableProps {
  clusters: ClustersResponse | null
  loading: boolean
}

function scoreColor(score: number): 'destructive' | 'warning' | 'secondary' {
  if (score >= 60) return 'destructive'
  if (score >= 30) return 'warning'
  return 'secondary'
}

function formatTime(iso: string | null): string {
  if (!iso) return '—'
  const d = new Date(iso)
  return `${d.toLocaleDateString([], { month: 'short', day: 'numeric' })} ${d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}`
}

function ClusterRow({ cluster }: { cluster: Cluster }) {
  const [expanded, setExpanded] = useState(false)

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
        <TableCell className="text-center">
          {cluster.density.toFixed(2)}
        </TableCell>
        <TableCell className="text-center">
          <Badge variant={scoreColor(cluster.coordinationScore)}>
            {cluster.coordinationScore.toFixed(1)}
          </Badge>
        </TableCell>
        <TableCell>
          <Badge variant="outline" className="text-xs">
            {cluster.clusterType || 'mixed'}
          </Badge>
        </TableCell>
      </TableRow>

      {expanded && cluster.members.length > 0 && (
        <TableRow>
          <TableCell colSpan={6} className="bg-muted/30 py-2 px-8">
            <div className="text-xs text-muted-foreground mb-1.5 font-medium">
              Members (top {cluster.members.length} by centrality):
            </div>
            <div className="flex flex-wrap gap-2">
              {cluster.members.map((member, idx) => (
                <Badge
                  key={idx}
                  variant="secondary"
                  className="font-mono text-xs"
                >
                  {member.accountId}
                  <span className="ml-1.5 text-muted-foreground">
                    ({member.centrality.toFixed(2)})
                  </span>
                </Badge>
              ))}
            </div>
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
          <CardTitle className="text-lg flex items-center gap-2">
            <Network className="h-5 w-5 text-muted-foreground" />
            Detected Clusters
          </CardTitle>
          <Badge variant="secondary">
            {clusterList.length} {clusterList.length === 1 ? 'cluster' : 'clusters'}
          </Badge>
        </div>
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
                <TableHead>Detected</TableHead>
                <TableHead className="text-center">Members</TableHead>
                <TableHead className="text-center">Density</TableHead>
                <TableHead className="text-center">Score</TableHead>
                <TableHead>Type</TableHead>
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
