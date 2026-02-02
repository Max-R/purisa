/**
 * Account type definitions
 */

export interface Account {
  id: string
  username: string
  displayName?: string
  platform: 'bluesky' | 'hackernews' | 'mastodon'
  createdAt: string
  followerCount: number
  followingCount: number
  postCount: number
  metadata: Record<string, any>
  firstSeen?: string
  lastAnalyzed?: string
}

export interface AccountCommentStats {
  totalComments: number
  inflammatoryCount: number
  inflammatoryRatio: number
  repetitiveCount: number
}

export interface AccountWithScore {
  account: Account
  score: Score
  commentStats?: AccountCommentStats | null
}

export interface Score {
  totalScore: number
  signals: Record<string, number>
  flagged: boolean
  threshold?: number
  lastUpdated?: string
}
