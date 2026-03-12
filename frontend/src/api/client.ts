/**
 * API client for Purisa backend
 */
import axios, { AxiosInstance } from 'axios'
import type { AccountWithScore } from '../types/account'
import type { Post } from '../types/post'
import type { Stats, CommentStats } from '../types/detection'
import type { ScheduledJob, JobExecution, CreateJobParams, UpdateJobParams } from '../types/schedule'
import type {
  TimelineResponse, TimelinePoint,
  ClustersResponse, Cluster, ClusterMember,
  CoordinationStats, PeriodStats,
  SpikesResponse, Spike,
  QueriesResponse, QueryInfo,
} from '../types/coordination'

class ApiClient {
  private client: AxiosInstance

  constructor(baseURL: string = 'http://localhost:8000/api') {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })
  }

  /**
   * Health check
   */
  async healthCheck() {
    const response = await this.client.get('/health')
    return response.data
  }

  /**
   * Get platform status
   */
  async getPlatformStatus() {
    const response = await this.client.get('/platforms/status')
    return response.data
  }

  /**
   * Transform API response to match frontend types
   */
  private transformAccount(apiAccount: any): AccountWithScore {
    const result: AccountWithScore = {
      account: {
        id: apiAccount.account.id,
        username: apiAccount.account.username,
        displayName: apiAccount.account.display_name,
        platform: apiAccount.account.platform,
        createdAt: apiAccount.account.created_at,
        followerCount: apiAccount.account.follower_count,
        followingCount: 0, // Not provided by API
        postCount: apiAccount.account.post_count,
        metadata: apiAccount.account.metadata,
        firstSeen: apiAccount.account.first_seen,
        lastAnalyzed: apiAccount.account.last_analyzed
      },
      score: {
        totalScore: apiAccount.score.total_score,
        signals: apiAccount.score.signals,
        flagged: apiAccount.score.flagged,
        threshold: apiAccount.score.threshold,
        lastUpdated: apiAccount.score.last_updated
      }
    }

    // Include comment stats if present
    if (apiAccount.comment_stats !== undefined) {
      result.commentStats = apiAccount.comment_stats ? {
        totalComments: apiAccount.comment_stats.total_comments,
        inflammatoryCount: apiAccount.comment_stats.inflammatory_count,
        inflammatoryRatio: apiAccount.comment_stats.inflammatory_ratio,
        repetitiveCount: apiAccount.comment_stats.repetitive_count
      } : null
    }

    return result
  }

  /**
   * Get all accounts with scores (paginated)
   */
  async getAllAccounts(
    platform?: string,
    limit: number = 50,
    offset: number = 0,
    includeCommentStats: boolean = false
  ): Promise<{ accounts: AccountWithScore[]; total: number }> {
    const params: any = { limit, offset, include_comment_stats: includeCommentStats }
    if (platform) {
      params.platform = platform
    }

    const response = await this.client.get('/accounts/all', { params })
    return {
      accounts: response.data.accounts.map((acc: any) => this.transformAccount(acc)),
      total: response.data.total
    }
  }

  /**
   * Get flagged accounts (paginated)
   */
  async getFlaggedAccounts(
    platform?: string,
    limit: number = 50,
    offset: number = 0,
    includeCommentStats: boolean = false
  ): Promise<{ accounts: AccountWithScore[]; total: number }> {
    const params: any = { limit, offset, include_comment_stats: includeCommentStats }
    if (platform) {
      params.platform = platform
    }

    const response = await this.client.get('/accounts/flagged', { params })
    return {
      accounts: response.data.accounts.map((acc: any) => this.transformAccount(acc)),
      total: response.data.total
    }
  }

  /**
   * Get account detail
   */
  async getAccountDetail(platform: string, accountId: string) {
    const response = await this.client.get(`/accounts/${platform}/${accountId}`)
    return response.data
  }

  /**
   * Get posts
   */
  async getPosts(platform?: string, flagged: boolean = false, limit: number = 50): Promise<Post[]> {
    const params: any = { limit, flagged }
    if (platform) {
      params.platform = platform
    }

    const response = await this.client.get('/posts', { params })
    return response.data.posts
  }

  /**
   * Get overview statistics
   */
  async getStats(platform?: string): Promise<Stats> {
    const params: any = {}
    if (platform) {
      params.platform = platform
    }

    const response = await this.client.get('/stats/overview', { params })
    const data = response.data

    // Transform snake_case to camelCase
    return {
      totalAccounts: data.total_accounts,
      totalPosts: data.total_posts,
      flaggedAccounts: data.flagged_accounts,
      totalFlags: data.total_flags,
      flagRate: data.flag_rate,
      platformBreakdown: data.platform_breakdown
    }
  }

  /**
   * Get comment statistics
   */
  async getCommentStats(platform?: string): Promise<CommentStats> {
    const params: any = {}
    if (platform) {
      params.platform = platform
    }

    const response = await this.client.get('/stats/comments', { params })
    const data = response.data

    // Transform snake_case to camelCase
    return {
      totalCommentsCollected: data.total_comments_collected,
      topPerformingPosts: data.top_performing_posts,
      postsWithCommentsHarvested: data.posts_with_comments_harvested,
      inflammatoryFlags: data.inflammatory_flags,
      uniqueAccountsFlagged: data.unique_accounts_flagged,
      avgSeverity: data.avg_severity,
      categoryBreakdown: data.category_breakdown
    }
  }

  /**
   * Trigger collection with query
   */
  async triggerCollection(options: {
    platform?: string
    query?: string
    limit?: number
    harvestComments?: boolean
  } = {}): Promise<CollectionResult> {
    const params: any = {}
    if (options.platform) params.platform = options.platform
    if (options.query) params.query = options.query
    if (options.limit) params.limit = options.limit
    if (options.harvestComments !== undefined) params.harvest_comments = options.harvestComments

    const response = await this.client.post('/collection/trigger', null, { params, timeout: 300000 })
    const data = response.data

    return {
      status: data.status,
      platform: data.platform,
      query: data.query,
      limit: data.limit,
      postsCollected: data.posts_collected,
      accountsDiscovered: data.accounts_discovered,
      commentsCollected: data.comments_collected,
      message: data.message,
      timestamp: data.timestamp
    }
  }

  /**
   * Get all comments made by an account
   */
  async getAccountComments(
    platform: string,
    accountId: string,
    limit: number = 100,
    offset: number = 0,
    includeInflammatoryFlags: boolean = true
  ): Promise<AccountCommentsResult> {
    const params = {
      limit,
      offset,
      include_inflammatory_flags: includeInflammatoryFlags
    }

    const response = await this.client.get(`/accounts/${platform}/${accountId}/comments`, { params })
    const data = response.data

    return {
      accountId: data.account_id,
      platform: data.platform,
      username: data.username,
      totalComments: data.total_comments,
      limit: data.limit,
      offset: data.offset,
      comments: data.comments.map((c: any) => ({
        id: c.id,
        content: c.content,
        createdAt: c.created_at,
        engagement: c.engagement,
        parentId: c.parent_id,
        parentPreview: c.parent_preview ? {
          id: c.parent_preview.id,
          contentSnippet: c.parent_preview.content_snippet,
          accountId: c.parent_preview.account_id
        } : null,
        inflammatory: c.inflammatory ? {
          severityScore: c.inflammatory.severity_score,
          triggeredCategories: c.inflammatory.triggered_categories,
          toxicityScores: c.inflammatory.toxicity_scores
        } : null
      }))
    }
  }

  /**
   * Trigger analysis
   */
  async triggerAnalysis(options: {
    accountId?: string
    platform?: string
  } = {}): Promise<AnalysisResult> {
    const params: any = {}
    if (options.accountId) params.account_id = options.accountId
    if (options.platform) params.platform = options.platform

    const response = await this.client.post('/analysis/trigger', null, { params, timeout: 300000 })
    const data = response.data

    return {
      status: data.status,
      message: data.message,
      totalAnalyzed: data.total_analyzed,
      newlyFlagged: data.newly_flagged,
      score: data.score ? {
        totalScore: data.score.total_score,
        signals: data.score.signals,
        flagged: data.score.flagged
      } : undefined
    }
  }

  // ─── Scheduled Jobs ───────────────────────────────────────

  /**
   * Transform API job response to frontend type
   */
  private transformJob(raw: any): ScheduledJob {
    return {
      id: raw.id,
      name: raw.name,
      platform: raw.platform,
      queries: raw.queries || [],
      cronExpression: raw.cron_expression,
      collectLimit: raw.collect_limit,
      analysisHours: raw.analysis_hours,
      harvestComments: Boolean(raw.harvest_comments),
      enabled: Boolean(raw.enabled),
      createdAt: raw.created_at,
      updatedAt: raw.updated_at,
      nextRunAt: raw.next_run_at || null,
      lastExecution: raw.last_execution ? this.transformExecution(raw.last_execution) : null,
    }
  }

  /**
   * Transform API execution response to frontend type
   */
  private transformExecution(raw: any): JobExecution {
    return {
      id: raw.id,
      jobId: raw.job_id,
      status: raw.status,
      startedAt: raw.started_at,
      completedAt: raw.completed_at,
      durationSeconds: raw.duration_seconds,
      postsCollected: raw.posts_collected,
      accountsDiscovered: raw.accounts_discovered,
      commentsCollected: raw.comments_collected,
      coordinationScore: raw.coordination_score,
      clustersDetected: raw.clusters_detected,
      errorMessage: raw.error_message,
    }
  }

  /**
   * List all scheduled jobs
   */
  async getJobs(platform?: string): Promise<ScheduledJob[]> {
    const params: any = {}
    if (platform) params.platform = platform

    const response = await this.client.get('/jobs', { params })
    return response.data.jobs.map((j: any) => this.transformJob(j))
  }

  /**
   * Create a new scheduled job
   */
  async createJob(params: CreateJobParams): Promise<ScheduledJob> {
    const body: any = {
      name: params.name,
      platform: params.platform,
      queries: params.queries,
      cronExpression: params.cronExpression,
    }
    if (params.collectLimit !== undefined) body.collectLimit = params.collectLimit
    if (params.analysisHours !== undefined) body.analysisHours = params.analysisHours
    if (params.harvestComments !== undefined) body.harvestComments = params.harvestComments

    const response = await this.client.post('/jobs', body)
    return this.transformJob(response.data)
  }

  /**
   * Update a scheduled job
   */
  async updateJob(jobId: number, params: UpdateJobParams): Promise<ScheduledJob> {
    const body: any = {}
    if (params.name !== undefined) body.name = params.name
    if (params.queries !== undefined) body.queries = params.queries
    if (params.cronExpression !== undefined) body.cronExpression = params.cronExpression
    if (params.collectLimit !== undefined) body.collectLimit = params.collectLimit
    if (params.analysisHours !== undefined) body.analysisHours = params.analysisHours
    if (params.harvestComments !== undefined) body.harvestComments = params.harvestComments
    if (params.enabled !== undefined) body.enabled = params.enabled

    const response = await this.client.put(`/jobs/${jobId}`, body)
    return this.transformJob(response.data)
  }

  /**
   * Delete a scheduled job
   */
  async deleteJob(jobId: number): Promise<void> {
    await this.client.delete(`/jobs/${jobId}`)
  }

  /**
   * Trigger immediate execution of a job
   */
  async runJobNow(jobId: number): Promise<{ status: string; execution_id: number }> {
    const response = await this.client.post(`/jobs/${jobId}/run`)
    return response.data
  }

  /**
   * Get execution history for a job
   */
  async getJobHistory(jobId: number, limit: number = 20, offset: number = 0): Promise<{ executions: JobExecution[]; total: number }> {
    const response = await this.client.get(`/jobs/${jobId}/history`, {
      params: { limit, offset }
    })
    return {
      executions: response.data.executions.map((e: any) => this.transformExecution(e)),
      total: response.data.total,
    }
  }

  // ─── Coordination Detection ────────────────────────────────

  /**
   * Get coordination score timeline
   */
  async getCoordinationTimeline(platform: string, hours: number = 168, query?: string): Promise<TimelineResponse> {
    const params: any = { platform, hours }
    if (query) params.query = query
    const response = await this.client.get('/coordination/timeline', { params })
    const d = response.data
    return {
      platform: d.platform,
      hours: d.hours,
      timeline: d.timeline.map((t: any): TimelinePoint => ({
        time: t.time,
        score: t.score,
        posts: t.posts,
        coordinated: t.coordinated,
        clusters: t.clusters,
        syncRate: t.sync_rate,
      })),
      summary: {
        dataPoints: d.summary.data_points,
        averageScore: d.summary.average_score,
        peakScore: d.summary.peak_score,
        totalPostsAnalyzed: d.summary.total_posts_analyzed,
        totalCoordinated: d.summary.total_coordinated,
      },
    }
  }

  /**
   * Get detected coordination clusters
   */
  async getCoordinationClusters(platform: string, hours: number = 24, query?: string): Promise<ClustersResponse> {
    const params: any = { platform, hours }
    if (query) params.query = query
    const response = await this.client.get('/coordination/clusters', { params })
    const d = response.data
    return {
      platform: d.platform,
      hours: d.hours,
      total: d.total,
      clusters: d.clusters.map((c: any): Cluster => ({
        clusterId: c.cluster_id,
        detectedAt: c.detected_at,
        timeWindow: {
          start: c.time_window?.start ?? null,
          end: c.time_window?.end ?? null,
        },
        memberCount: c.member_count,
        density: c.density,
        clusterType: c.cluster_type,
        coordinationScore: c.coordination_score,
        members: (c.members || []).map((m: any): ClusterMember => ({
          accountId: m.account_id,
          centrality: m.centrality,
        })),
      })),
    }
  }

  /**
   * Get coordination stats summary
   */
  async getCoordinationStats(platform?: string, query?: string): Promise<CoordinationStats> {
    const params: any = {}
    if (platform) params.platform = platform
    if (query) params.query = query

    const response = await this.client.get('/coordination/stats', { params })
    const d = response.data

    const transformPeriod = (p: any): PeriodStats => ({
      avgScore: p.avg_score,
      peakScore: p.peak_score,
      totalPosts: p.total_posts,
      totalCoordinated: p.total_coordinated,
      hoursAnalyzed: p.hours_analyzed,
    })

    return {
      platform: d.platform,
      totalClustersDetected: d.total_clusters_detected,
      last24h: transformPeriod(d.last_24h),
      last7d: transformPeriod(d.last_7d),
    }
  }

  /**
   * Get coordination spikes
   */
  async getCoordinationSpikes(platform: string, hours: number = 168, query?: string): Promise<SpikesResponse> {
    const params: any = { platform, hours }
    if (query) params.query = query
    const response = await this.client.get('/coordination/spikes', { params })
    const d = response.data
    return {
      platform: d.platform,
      hours: d.hours,
      thresholdStd: d.threshold_std,
      total: d.total,
      spikes: d.spikes.map((s: any): Spike => ({
        timeBucket: s.time_bucket,
        coordinationScore: s.coordination_score,
        zScore: s.z_score,
        totalPosts: s.total_posts,
        clusterCount: s.cluster_count,
        baselineMedian: s.baseline_median,
        baselineMadStd: s.baseline_mad_std,
      })),
    }
  }

  /**
   * Get distinct source queries with post counts for a platform
   */
  async getCoordinationQueries(platform: string, hours: number = 168): Promise<QueriesResponse> {
    const response = await this.client.get('/coordination/queries', {
      params: { platform, hours }
    })
    const d = response.data
    return {
      platform: d.platform,
      hours: d.hours,
      totalQueries: d.total_queries,
      queries: d.queries.map((q: any): QueryInfo => ({
        query: q.query,
        postCount: q.post_count,
        earliest: q.earliest,
        latest: q.latest,
      })),
    }
  }
}

// Result types
export interface CollectionResult {
  status: string
  platform?: string
  query?: string
  limit?: number
  postsCollected: number
  accountsDiscovered: number
  commentsCollected: number
  message: string
  timestamp: string
}

export interface AnalysisResult {
  status: string
  message: string
  totalAnalyzed?: number
  newlyFlagged?: number
  score?: {
    totalScore: number
    signals: Record<string, number>
    flagged: boolean
  }
}

export interface AccountComment {
  id: string
  content: string
  createdAt: string | null
  engagement: Record<string, number>
  parentId: string | null
  parentPreview: {
    id: string
    contentSnippet: string | null
    accountId: string
  } | null
  inflammatory: {
    severityScore: number
    triggeredCategories: string[]
    toxicityScores: Record<string, number>
  } | null
}

export interface AccountCommentsResult {
  accountId: string
  platform: string
  username: string
  totalComments: number
  limit: number
  offset: number
  comments: AccountComment[]
}

// Export singleton instance
export const apiClient = new ApiClient()
