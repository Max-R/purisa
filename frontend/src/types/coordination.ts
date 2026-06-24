/**
 * Types for coordination detection API responses.
 */

// ─── Timeline ─────────────────────────────────────────────

export interface TimelinePoint {
  time: string
  score: number
  posts: number
  coordinated: number
  clusters: number
  syncRate: number
}

export interface TimelineSummary {
  dataPoints: number
  averageScore: number
  peakScore: number
  totalPostsAnalyzed: number
  totalCoordinated: number
}

export interface TimelineResponse {
  platform: string
  hours: number
  timeline: TimelinePoint[]
  summary: TimelineSummary
}

// ─── Clusters ─────────────────────────────────────────────

export interface EdgeTypeDistribution {
  [edgeType: string]: number
}

export interface SyncPostingPattern {
  count: number
  avgTimeDiffSeconds: number
  minTimeDiffSeconds: number
  maxTimeDiffSeconds: number
}

export interface UrlSharingPattern {
  count: number
  sharedUrls: string[]
}

export interface TextSimilarityPattern {
  count: number
  avgSimilarity: number
  sampleSnippets: { text: string; similarity: number }[]
}

export interface HashtagPattern {
  count: number
  sharedHashtags: string[]
}

export interface ReplyPattern {
  count: number
}

export interface ClusterPatterns {
  edgeTypeDistribution: EdgeTypeDistribution
  syncPosting?: SyncPostingPattern
  urlSharing?: UrlSharingPattern
  textSimilarity?: TextSimilarityPattern
  hashtagOverlap?: HashtagPattern
  replyPattern?: ReplyPattern
}

export interface Cluster {
  clusterId: string
  detectedAt: string | null
  timeWindow: {
    start: string | null
    end: string | null
  }
  memberCount: number
  edgeCount: number
  density: number
  clusterType: string
  coordinationScore: number
  patterns: ClusterPatterns
}

export interface ClustersResponse {
  platform: string
  hours: number
  clusters: Cluster[]
  total: number
}

// ─── Stats ────────────────────────────────────────────────

export interface PeriodStats {
  avgScore: number
  peakScore: number
  totalPosts: number
  totalCoordinated: number
  hoursAnalyzed: number
}

export interface CoordinationStats {
  platform: string
  totalClustersDetected: number
  last24h: PeriodStats
  last7d: PeriodStats
}

// ─── Spikes ───────────────────────────────────────────────

export interface Spike {
  timeBucket: string
  coordinationScore: number
  zScore: number
  totalPosts: number
  clusterCount: number
  baselineMedian: number
  baselineMadStd: number
}

export interface SpikesResponse {
  platform: string
  hours: number
  thresholdStd: number
  spikes: Spike[]
  total: number
}

// ─── Queries ─────────────────────────────────────────────

export interface QueryInfo {
  query: string
  postCount: number
  earliest: string | null
  latest: string | null
}

export interface QueriesResponse {
  platform: string
  hours: number
  queries: QueryInfo[]
  totalQueries: number
}
