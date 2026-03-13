import { useState, useCallback, useEffect } from 'react'
import { usePlatforms } from './hooks/usePlatforms'
import { useCoordination } from './hooks/useCoordination'
import { useScheduledJobs } from './hooks/useScheduledJobs'
import { apiClient } from './api/client'
import type { QueriesResponse } from './types/coordination'
import PlatformFilter from './components/PlatformFilter'
import ThemeToggle from './components/ThemeToggle'
import CollectionPanel from './components/CollectionPanel'
import SchedulePanel from './components/SchedulePanel'
import DataContextBanner from './components/DataContextBanner'
import SpikesAlert from './components/SpikesAlert'
import CoordinationStatsCards from './components/CoordinationStatsCards'
import CoordinationTimeline from './components/CoordinationTimeline'
import ClustersTable from './components/ClustersTable'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from "@/components/ui/button"
import { Shield, Info, X } from "lucide-react"

export default function App() {
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)
  const [selectedQuery, setSelectedQuery] = useState<string | null>(null)
  const [showExplainer, setShowExplainer] = useState(true)
  const [queriesData, setQueriesData] = useState<QueriesResponse | null>(null)

  const { platforms } = usePlatforms()
  const { jobs, fetchJobs } = useScheduledJobs()

  // Auto-select first platform so coordination endpoints get called
  useEffect(() => {
    if (!selectedPlatform && platforms.length > 0) {
      setSelectedPlatform(platforms[0])
    }
  }, [platforms, selectedPlatform])

  // Fetch jobs and queries when platform changes
  useEffect(() => {
    if (selectedPlatform) {
      fetchJobs()
      apiClient.getCoordinationQueries(selectedPlatform, 168)
        .then(setQueriesData)
        .catch((e) => console.error('Failed to load queries:', e))
    }
  }, [selectedPlatform, fetchJobs])

  // Clear query filter when platform changes
  useEffect(() => {
    setSelectedQuery(null)
  }, [selectedPlatform])

  const {
    timeline,
    clusters,
    stats,
    spikes,
    loading: coordinationLoading,
    refetch: refetchCoordination,
  } = useCoordination(selectedPlatform || undefined, selectedQuery || undefined)

  const handlePlatformChange = useCallback((platform: string | null) => {
    setSelectedPlatform(platform)
  }, [])

  const handleRefresh = useCallback(async () => {
    await refetchCoordination()
    // Also refresh queries data after collection/job completes
    if (selectedPlatform) {
      apiClient.getCoordinationQueries(selectedPlatform, 168)
        .then(setQueriesData)
        .catch((e) => console.error('Failed to refresh queries:', e))
    }
  }, [refetchCoordination, selectedPlatform])

  const handleCollectionComplete = useCallback((query: string) => {
    setSelectedQuery(query)
    handleRefresh()
  }, [handleRefresh])

  const handleTimelineHoursChange = useCallback(async () => {
    await refetchCoordination()
  }, [refetchCoordination])

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-10 w-10 rounded-lg bg-primary flex items-center justify-center">
                <Shield className="h-6 w-6 text-primary-foreground" />
              </div>
              <div>
                <h1 className="text-xl font-bold">Purisa</h1>
                <p className="text-sm text-muted-foreground">Coordination Detection Dashboard</p>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <PlatformFilter
                platforms={platforms}
                selected={selectedPlatform}
                onChange={handlePlatformChange}
              />
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* What is Coordination Detection? */}
          {showExplainer && (
            <Card className="border-blue-200 bg-blue-50/50 dark:bg-blue-950/20 dark:border-blue-800/50">
              <CardContent className="py-4 px-5">
                <div className="flex items-start justify-between gap-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Info className="h-5 w-5 text-blue-600 dark:text-blue-400 shrink-0" />
                      <h3 className="font-semibold text-sm">What is Coordination Detection?</h3>
                    </div>
                    <p className="text-sm text-muted-foreground leading-relaxed">
                      This dashboard detects <strong className="text-foreground">coordinated inauthentic behavior</strong> — groups of accounts
                      that act together in suspicious patterns, like posting the same content simultaneously,
                      sharing the same links, or using identical hashtags within seconds of each other.
                      A high coordination score does not prove malicious intent — it flags patterns worth investigating.
                    </p>
                    <div className="flex flex-wrap gap-4 text-xs text-muted-foreground pt-1">
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-red-500" />
                        Score 60+ = High coordination
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-yellow-500" />
                        Score 30–59 = Moderate
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="inline-block h-2.5 w-2.5 rounded-full bg-gray-400" />
                        Score 0–29 = Low / organic
                      </span>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 w-7 p-0 shrink-0 text-muted-foreground"
                    onClick={() => setShowExplainer(false)}
                  >
                    <X className="h-4 w-4" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Collection Panel */}
          <CollectionPanel
            platforms={platforms.length > 0 ? platforms : ['bluesky', 'hackernews']}
            onComplete={handleRefresh}
            onCollectionComplete={handleCollectionComplete}
          />

          {/* Scheduled Jobs */}
          <SchedulePanel
            platforms={platforms.length > 0 ? platforms : ['bluesky', 'hackernews']}
            onJobComplete={handleRefresh}
          />

          {/* Data Context Banner */}
          {selectedPlatform && (
            <DataContextBanner
              platform={selectedPlatform}
              queries={queriesData}
              jobs={jobs}
              selectedQuery={selectedQuery}
              onQueryChange={setSelectedQuery}
            />
          )}

          {/* Spikes Alert */}
          <SpikesAlert spikes={spikes} />

          {/* Coordination Stats */}
          <CoordinationStatsCards
            stats={stats}
            loading={coordinationLoading}
          />

          {/* Coordination Timeline */}
          <CoordinationTimeline
            timeline={timeline}
            loading={coordinationLoading}
            onHoursChange={handleTimelineHoursChange}
          />

          {/* Detected Clusters */}
          <ClustersTable
            clusters={clusters}
            loading={coordinationLoading}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-8">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Purisa Coordination Detection</span>
            </div>
            <p className="text-xs text-muted-foreground max-w-md text-center sm:text-right">
              Coordination scores indicate statistical patterns and should be verified manually.
              High scores do not necessarily indicate malicious intent.
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
