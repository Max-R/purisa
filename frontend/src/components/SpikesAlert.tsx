/**
 * Spikes alert banner.
 *
 * Shows when coordination spikes are detected above baseline.
 * Only renders when spikes array is non-empty.
 */
import { useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { AlertTriangle, X, ChevronDown, ChevronUp } from 'lucide-react'
import InfoTooltip from './InfoTooltip'
import type { SpikesResponse } from '../types/coordination'

interface SpikesAlertProps {
  spikes: SpikesResponse | null
}

export default function SpikesAlert({ spikes }: SpikesAlertProps) {
  const [dismissed, setDismissed] = useState(false)
  const [expanded, setExpanded] = useState(false)

  if (!spikes || spikes.spikes.length === 0 || dismissed) {
    return null
  }

  const spikeList = spikes.spikes
  const highestZScore = Math.max(...spikeList.map(s => s.zScore))
  const highestScore = Math.max(...spikeList.map(s => s.coordinationScore))

  return (
    <Card className="border-amber-500/50 bg-amber-50 dark:bg-amber-950/20">
      <CardContent className="py-3 px-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-600 dark:text-amber-400 shrink-0" />
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-medium text-amber-900 dark:text-amber-100">
                {spikeList.length} coordination {spikeList.length === 1 ? 'spike' : 'spikes'} detected
              </span>
              <InfoTooltip
                text="A spike occurs when an hourly coordination score is significantly above the historical baseline (using Median Absolute Deviation). This may indicate a sudden burst of coordinated activity."
                side="bottom"
              />
              <Badge
                variant="outline"
                className="border-amber-500 text-amber-700 dark:text-amber-300"
                title="Z-score measures how far above the baseline this spike is. Higher values = more unusual."
              >
                {highestZScore.toFixed(1)}x above baseline
              </Badge>
              <Badge variant="outline" className="border-amber-500 text-amber-700 dark:text-amber-300">
                Max score: {highestScore.toFixed(1)}
              </Badge>
            </div>
          </div>

          <div className="flex items-center gap-1 shrink-0">
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-amber-700 dark:text-amber-300 hover:bg-amber-200/50 dark:hover:bg-amber-800/50"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
            <Button
              variant="ghost"
              size="sm"
              className="h-7 w-7 p-0 text-amber-700 dark:text-amber-300 hover:bg-amber-200/50 dark:hover:bg-amber-800/50"
              onClick={() => setDismissed(true)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {expanded && (
          <div className="mt-3 space-y-1.5">
            {spikeList.map((spike, i) => {
              const time = new Date(spike.timeBucket)
              return (
                <div
                  key={i}
                  className="flex items-center gap-3 text-sm text-amber-800 dark:text-amber-200 pl-8"
                >
                  <span className="font-mono text-xs">
                    {time.toLocaleDateString()} {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </span>
                  <span>Score: {spike.coordinationScore.toFixed(1)}</span>
                  <span
                    className="text-muted-foreground"
                    title={`Z-score: ${spike.zScore.toFixed(2)} — measures standard deviations above the median coordination score`}
                  >
                    {spike.zScore.toFixed(1)}x above normal
                  </span>
                  <span className="text-muted-foreground">{spike.totalPosts} posts</span>
                  <span className="text-muted-foreground">{spike.clusterCount} clusters</span>
                </div>
              )
            })}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
