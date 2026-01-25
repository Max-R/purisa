/**
 * Detection type definitions
 */

export interface Flag {
  accountId: string
  flagType: string
  confidenceScore: number
  reason: string
  timestamp: string
}

export interface Stats {
  totalAccounts: number
  totalPosts: number
  flaggedAccounts: number
  totalFlags: number
  flagRate: number
  platformBreakdown: Record<string, PlatformStats>
}

export interface PlatformStats {
  accounts: number
  posts: number
}

export interface CommentStats {
  totalCommentsCollected: number
  topPerformingPosts: number
  postsWithCommentsHarvested: number
  inflammatoryFlags: number
  uniqueAccountsFlagged: number
  avgSeverity: number
  categoryBreakdown: Record<string, number>
}
