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

export interface ClusterMember {
  accountId: string
  centrality: number
}

export interface Cluster {
  clusterId: string
  detectedAt: string | null
  timeWindow: {
    start: string | null
    end: string | null
  }
  memberCount: number
  density: number
  clusterType: string
  coordinationScore: number
  members: ClusterMember[]
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
