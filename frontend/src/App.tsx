import { useState, useCallback } from 'react'
import { usePlatforms } from './hooks/usePlatforms'
import { useCoordination } from './hooks/useCoordination'
import PlatformFilter from './components/PlatformFilter'
import ThemeToggle from './components/ThemeToggle'
import CollectionPanel from './components/CollectionPanel'
import SchedulePanel from './components/SchedulePanel'
import SpikesAlert from './components/SpikesAlert'
import CoordinationStatsCards from './components/CoordinationStatsCards'
import CoordinationTimeline from './components/CoordinationTimeline'
import ClustersTable from './components/ClustersTable'
import { Button } from "@/components/ui/button"
import { RefreshCw, Shield } from "lucide-react"

export default function App() {
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)

  const { platforms } = usePlatforms()
  const {
    timeline,
    clusters,
    stats,
    spikes,
    loading: coordinationLoading,
    refetch: refetchCoordination,
  } = useCoordination(selectedPlatform || undefined)

  const handlePlatformChange = useCallback((platform: string | null) => {
    setSelectedPlatform(platform)
  }, [])

  const handleRefresh = useCallback(async () => {
    await refetchCoordination()
  }, [refetchCoordination])

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
              <Button
                onClick={handleRefresh}
                disabled={coordinationLoading}
                variant="outline"
              >
                <RefreshCw className={`h-4 w-4 ${coordinationLoading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline ml-2">
                  {coordinationLoading ? 'Refreshing...' : 'Refresh'}
                </span>
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-8">
          {/* Collection Panel */}
          <CollectionPanel
            platforms={platforms.length > 0 ? platforms : ['bluesky', 'hackernews']}
            onComplete={handleRefresh}
          />

          {/* Scheduled Jobs */}
          <SchedulePanel
            platforms={platforms.length > 0 ? platforms : ['bluesky', 'hackernews']}
            onJobComplete={handleRefresh}
          />

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
            <p className="text-xs text-muted-foreground">
              Scores indicate coordination probability and should be verified manually
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
