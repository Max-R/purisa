/**
 * Post type definitions
 */

export interface Post {
  id: string
  accountId: string
  platform: string
  content: string
  createdAt: string
  engagement: {
    likes?: number
    reposts?: number
    replies?: number
    score?: number
    comments?: number
  }
  metadata: Record<string, any>
}
