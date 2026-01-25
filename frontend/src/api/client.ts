/**
 * API client for Purisa backend
 */
import axios, { AxiosInstance } from 'axios'
import type { AccountWithScore } from '../types/account'
import type { Post } from '../types/post'
import type { Stats, CommentStats } from '../types/detection'

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
    return {
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
  }

  /**
   * Get all accounts with scores (paginated)
   */
  async getAllAccounts(
    platform?: string,
    limit: number = 50,
    offset: number = 0
  ): Promise<{ accounts: AccountWithScore[]; total: number }> {
    const params: any = { limit, offset }
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
    offset: number = 0
  ): Promise<{ accounts: AccountWithScore[]; total: number }> {
    const params: any = { limit, offset }
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

// Export singleton instance
export const apiClient = new ApiClient()
