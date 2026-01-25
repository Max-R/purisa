import { useState, useEffect, useCallback } from 'react'
import { useStats } from './hooks/useStats'
import { useAccounts } from './hooks/useAccounts'
import { usePlatforms } from './hooks/usePlatforms'
import StatsCards from './components/StatsCards'
import AccountsTable from './components/AccountsTable'
import PlatformFilter from './components/PlatformFilter'
import ThemeToggle from './components/ThemeToggle'
import CollectionPanel from './components/CollectionPanel'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { RefreshCw, Shield, ChevronLeft, ChevronRight } from "lucide-react"

export default function App() {
  const [selectedPlatform, setSelectedPlatform] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<string>('all')
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  const { stats, commentStats, loading: statsLoading, refetch: refetchStats } = useStats(selectedPlatform || undefined)
  const {
    allAccounts,
    flaggedAccounts,
    allAccountsTotal,
    flaggedAccountsTotal,
    loading: accountsLoading,
    error: accountsError,
    fetchAll,
    fetchFlagged
  } = useAccounts()
  const { platforms } = usePlatforms()

  const pageSizeOptions = [50, 100, 250, 500, 1000]

  const displayedAccounts = activeTab === 'all' ? allAccounts : flaggedAccounts
  const totalItems = activeTab === 'all' ? allAccountsTotal : flaggedAccountsTotal
  const totalPages = Math.ceil(totalItems / pageSize)
  const startItem = totalItems > 0 ? (currentPage - 1) * pageSize + 1 : 0
  const endItem = Math.min(currentPage * pageSize, totalItems)

  useEffect(() => {
    fetchAll(undefined, pageSize, 0)
    fetchFlagged(undefined, pageSize, 0)
  }, [])

  const handlePlatformChange = useCallback(async (platform: string | null) => {
    setSelectedPlatform(platform)
    setCurrentPage(1)
    await Promise.all([
      fetchAll(platform || undefined, pageSize, 0),
      fetchFlagged(platform || undefined, pageSize, 0)
    ])
  }, [pageSize, fetchAll, fetchFlagged])

  const handleRefresh = useCallback(async () => {
    const offset = (currentPage - 1) * pageSize
    await Promise.all([
      refetchStats(),
      fetchAll(selectedPlatform || undefined, pageSize, offset),
      fetchFlagged(selectedPlatform || undefined, pageSize, offset)
    ])
  }, [currentPage, pageSize, selectedPlatform, refetchStats, fetchAll, fetchFlagged])

  const handleTabChange = useCallback(async (tab: string) => {
    setActiveTab(tab)
    setCurrentPage(1)
    if (tab === 'all') {
      await fetchAll(selectedPlatform || undefined, pageSize, 0)
    } else {
      await fetchFlagged(selectedPlatform || undefined, pageSize, 0)
    }
  }, [selectedPlatform, pageSize, fetchAll, fetchFlagged])

  const handlePageChange = useCallback(async (page: number) => {
    setCurrentPage(page)
    const offset = (page - 1) * pageSize
    if (activeTab === 'all') {
      await fetchAll(selectedPlatform || undefined, pageSize, offset)
    } else {
      await fetchFlagged(selectedPlatform || undefined, pageSize, offset)
    }
  }, [activeTab, selectedPlatform, pageSize, fetchAll, fetchFlagged])

  const handlePageSizeChange = useCallback(async (newSize: string) => {
    const size = parseInt(newSize)
    setPageSize(size)
    setCurrentPage(1)
    if (activeTab === 'all') {
      await fetchAll(selectedPlatform || undefined, size, 0)
    } else {
      await fetchFlagged(selectedPlatform || undefined, size, 0)
    }
  }, [activeTab, selectedPlatform, fetchAll, fetchFlagged])

  const isLoading = statsLoading || accountsLoading

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
                <p className="text-sm text-muted-foreground">Bot Detection Dashboard</p>
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
                disabled={isLoading}
                variant="outline"
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                <span className="hidden sm:inline ml-2">
                  {isLoading ? 'Refreshing...' : 'Refresh'}
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

          {/* Stats Cards */}
          <StatsCards
            stats={stats}
            commentStats={commentStats}
            loading={statsLoading}
          />

          {/* Score Legend */}
          <Card>
            <CardContent className="py-3 px-4">
              <div className="flex flex-wrap items-center gap-4 text-sm">
                <span className="font-medium">Risk Levels:</span>
                <div className="flex flex-wrap gap-3">
                  <Badge variant="destructive">High (8+)</Badge>
                  <Badge variant="warning">Medium (7-8)</Badge>
                  <Badge variant="success">Low (&lt;7)</Badge>
                </div>
                <span className="text-muted-foreground ml-auto text-xs">
                  Max: 22.0 | Threshold: 7.0
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Accounts Section */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
                <div>
                  <CardTitle>Accounts</CardTitle>
                  <CardDescription>
                    {activeTab === 'all'
                      ? 'All analyzed accounts with bot detection scores'
                      : 'Accounts flagged as potentially suspicious (score ≥7.0)'}
                  </CardDescription>
                </div>

                <Tabs value={activeTab} onValueChange={handleTabChange}>
                  <TabsList>
                    <TabsTrigger value="all">
                      All
                      <Badge variant="secondary" className="ml-2">
                        {allAccountsTotal.toLocaleString()}
                      </Badge>
                    </TabsTrigger>
                    <TabsTrigger value="flagged">
                      Flagged
                      <Badge
                        variant={flaggedAccountsTotal > 0 ? "destructive" : "secondary"}
                        className="ml-2"
                      >
                        {flaggedAccountsTotal.toLocaleString()}
                      </Badge>
                    </TabsTrigger>
                  </TabsList>
                </Tabs>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              <AccountsTable
                accounts={displayedAccounts}
                loading={accountsLoading}
                error={accountsError}
              />
            </CardContent>

            {/* Pagination */}
            <div className="border-t p-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-muted-foreground">
                    Showing {startItem.toLocaleString()} to {endItem.toLocaleString()} of {totalItems.toLocaleString()}
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="text-muted-foreground">Per page:</span>
                    <Select value={pageSize.toString()} onValueChange={handlePageSizeChange}>
                      <SelectTrigger className="w-[80px] h-8">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {pageSizeOptions.map((size) => (
                          <SelectItem key={size} value={size.toString()}>
                            {size}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {totalPages > 1 && (
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage - 1)}
                      disabled={currentPage === 1 || accountsLoading}
                    >
                      <ChevronLeft className="h-4 w-4" />
                      <span className="hidden sm:inline">Previous</span>
                    </Button>
                    <span className="text-sm text-muted-foreground px-2">
                      Page {currentPage} of {totalPages}
                    </span>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handlePageChange(currentPage + 1)}
                      disabled={currentPage === totalPages || accountsLoading}
                    >
                      <span className="hidden sm:inline">Next</span>
                      <ChevronRight className="h-4 w-4" />
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </Card>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t mt-8">
        <div className="container mx-auto px-4 py-4">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm text-muted-foreground">Purisa Bot Detection</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Scores are estimates and should be verified manually
            </p>
          </div>
        </div>
      </footer>
    </div>
  )
}
