import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Download, Play, BarChart3, Loader2, CheckCircle, AlertCircle, MessageSquare } from 'lucide-react'
import { apiClient, type CollectionResult, type AnalysisResult } from '../api/client'

interface CollectionPanelProps {
  platforms: string[]
  onComplete?: () => void
}

export default function CollectionPanel({ platforms, onComplete }: CollectionPanelProps) {
  const [platform, setPlatform] = useState<string>('bluesky')
  const [query, setQuery] = useState<string>('')
  const [limit, setLimit] = useState<number>(100)
  const [harvestComments, setHarvestComments] = useState<boolean>(true)

  const [isCollecting, setIsCollecting] = useState(false)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [collectionResult, setCollectionResult] = useState<CollectionResult | null>(null)
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleCollect = async () => {
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setIsCollecting(true)
    setError(null)
    setCollectionResult(null)

    try {
      const result = await apiClient.triggerCollection({
        platform,
        query: query.trim(),
        limit,
        harvestComments
      })
      setCollectionResult(result)
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Collection failed')
    } finally {
      setIsCollecting(false)
    }
  }

  const handleAnalyze = async () => {
    setIsAnalyzing(true)
    setError(null)
    setAnalysisResult(null)

    try {
      const result = await apiClient.triggerAnalysis({ platform })
      setAnalysisResult(result)
      onComplete?.()
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Analysis failed')
    } finally {
      setIsAnalyzing(false)
    }
  }

  const handleCollectAndAnalyze = async () => {
    await handleCollect()
    if (!error) {
      await handleAnalyze()
    }
  }

  const limitOptions = [50, 100, 250, 500, 1000, 2500, 5000]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="h-5 w-5" />
          Data Collection
        </CardTitle>
        <CardDescription>
          Collect posts from social media platforms and analyze for bot activity
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Platform and Query Row */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="text-sm font-medium mb-1.5 block">Platform</label>
            <Select value={platform} onValueChange={setPlatform}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {platforms.map((p) => (
                  <SelectItem key={p} value={p}>
                    {p.charAt(0).toUpperCase() + p.slice(1)}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="md:col-span-2">
            <label className="text-sm font-medium mb-1.5 block">Search Query</label>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder={platform === 'bluesky' ? '#hashtag or keyword' : 'top, new, or best'}
              className="w-full px-3 py-2 border rounded-md bg-background text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>

          <div>
            <label className="text-sm font-medium mb-1.5 block">Limit</label>
            <Select value={limit.toString()} onValueChange={(v) => setLimit(parseInt(v))}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {limitOptions.map((l) => (
                  <SelectItem key={l} value={l.toString()}>
                    {l.toLocaleString()} posts
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Options Row */}
        <div className="flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={harvestComments}
              onChange={(e) => setHarvestComments(e.target.checked)}
              className="rounded border-gray-300"
            />
            <MessageSquare className="h-4 w-4 text-muted-foreground" />
            Harvest comments from top posts
          </label>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-wrap gap-2">
          <Button
            onClick={handleCollect}
            disabled={isCollecting || isAnalyzing || !query.trim()}
            variant="outline"
          >
            {isCollecting ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Download className="h-4 w-4 mr-2" />
            )}
            Collect Only
          </Button>

          <Button
            onClick={handleAnalyze}
            disabled={isCollecting || isAnalyzing}
            variant="outline"
          >
            {isAnalyzing ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <BarChart3 className="h-4 w-4 mr-2" />
            )}
            Analyze Only
          </Button>

          <Button
            onClick={handleCollectAndAnalyze}
            disabled={isCollecting || isAnalyzing || !query.trim()}
          >
            {(isCollecting || isAnalyzing) ? (
              <Loader2 className="h-4 w-4 animate-spin mr-2" />
            ) : (
              <Play className="h-4 w-4 mr-2" />
            )}
            Collect & Analyze
          </Button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="flex items-center gap-2 p-3 bg-destructive/10 text-destructive rounded-md">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm">{error}</span>
          </div>
        )}

        {/* Results Display */}
        {(collectionResult || analysisResult) && (
          <div className="space-y-3 pt-2 border-t">
            {collectionResult && (
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">Collection Complete</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    <Badge variant="secondary">
                      {collectionResult.postsCollected.toLocaleString()} posts
                    </Badge>
                    <Badge variant="secondary">
                      {collectionResult.accountsDiscovered.toLocaleString()} accounts
                    </Badge>
                    {collectionResult.commentsCollected > 0 && (
                      <Badge variant="secondary">
                        {collectionResult.commentsCollected.toLocaleString()} comments
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            )}

            {analysisResult && (
              <div className="flex items-start gap-2">
                <CheckCircle className="h-4 w-4 text-green-500 mt-0.5" />
                <div className="text-sm">
                  <p className="font-medium">Analysis Complete</p>
                  <div className="flex flex-wrap gap-2 mt-1">
                    {analysisResult.totalAnalyzed !== undefined && (
                      <Badge variant="secondary">
                        {analysisResult.totalAnalyzed.toLocaleString()} analyzed
                      </Badge>
                    )}
                    {analysisResult.newlyFlagged !== undefined && analysisResult.newlyFlagged > 0 && (
                      <Badge variant="destructive">
                        {analysisResult.newlyFlagged} flagged
                      </Badge>
                    )}
                    {analysisResult.newlyFlagged === 0 && (
                      <Badge variant="success">
                        No suspicious accounts
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  )
}
