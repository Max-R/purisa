"""FastAPI routes and endpoints."""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy import func
import logging
from purisa.database.connection import get_database
from purisa.database.models import AccountDB, PostDB, FlagDB, ScoreDB, InflammatoryFlagDB, CommentStatsDB
from purisa.models.account import Account
from purisa.models.post import Post
from purisa.models.detection import Flag, Score
from purisa.services.collector import UniversalCollector
from purisa.services.analyzer import BotDetector
from purisa.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "Purisa Bot Detection API"
    }


@router.get("/platforms/status")
async def get_platform_status():
    """Get status of all configured platforms."""
    try:
        collector = UniversalCollector()
        available_platforms = collector.get_available_platforms()

        return {
            "available_platforms": available_platforms,
            "total_platforms": len(available_platforms)
        }
    except Exception as e:
        logger.error(f"Error getting platform status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/flagged")
async def get_flagged_accounts(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(50, ge=1, le=5000, description="Maximum number of accounts"),
    offset: int = Query(0, ge=0, description="Number of accounts to skip"),
    include_comment_stats: bool = Query(False, description="Include per-account comment statistics")
):
    """Get flagged accounts with pagination support."""
    try:
        db = get_database()

        with db.get_session() as session:
            # Build query with join to apply platform filter efficiently
            query = session.query(ScoreDB, AccountDB).join(
                AccountDB, ScoreDB.account_id == AccountDB.id
            ).filter(ScoreDB.flagged == 1)

            # Apply platform filter before pagination
            if platform:
                query = query.filter(AccountDB.platform == platform)

            # Get total count for pagination
            total_count = query.count()

            # Apply pagination
            scores_with_accounts = query.offset(offset).limit(limit).all()

            # Pre-fetch comment stats if requested
            comment_stats_map = {}
            if include_comment_stats:
                account_ids = [account.id for score, account in scores_with_accounts]
                if account_ids:
                    stats = session.query(CommentStatsDB).filter(
                        CommentStatsDB.account_id.in_(account_ids)
                    ).all()
                    comment_stats_map = {s.account_id: s for s in stats}

            results = []
            for score, account in scores_with_accounts:
                result = {
                    "account": {
                        "id": account.id,
                        "username": account.username,
                        "display_name": account.display_name,
                        "platform": account.platform,
                        "created_at": account.created_at.isoformat() if account.created_at else None,
                        "follower_count": account.follower_count,
                        "post_count": account.post_count,
                        "metadata": account.platform_metadata
                    },
                    "score": {
                        "total_score": score.total_score,
                        "signals": score.signals,
                        "flagged": bool(score.flagged),
                        "last_updated": score.last_updated.isoformat() if score.last_updated else None
                    }
                }

                # Add comment stats if requested
                if include_comment_stats:
                    stats = comment_stats_map.get(account.id)
                    if stats:
                        result["comment_stats"] = {
                            "total_comments": stats.total_comments,
                            "inflammatory_count": stats.inflammatory_comment_count,
                            "inflammatory_ratio": stats.inflammatory_ratio,
                            "repetitive_count": stats.repetitive_comment_count
                        }
                    else:
                        result["comment_stats"] = None

                results.append(result)

            return {
                "accounts": results,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }

    except Exception as e:
        logger.error(f"Error getting flagged accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/all")
async def get_all_accounts(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    limit: int = Query(50, ge=1, le=5000, description="Maximum number of accounts"),
    offset: int = Query(0, ge=0, description="Number of accounts to skip"),
    include_comment_stats: bool = Query(False, description="Include per-account comment statistics")
):
    """Get all accounts with their scores with pagination support."""
    try:
        db = get_database()

        with db.get_session() as session:
            # Build query with join to apply platform filter efficiently
            query = session.query(ScoreDB, AccountDB).join(
                AccountDB, ScoreDB.account_id == AccountDB.id
            ).order_by(ScoreDB.total_score.desc())

            # Apply platform filter before pagination
            if platform:
                query = query.filter(AccountDB.platform == platform)

            # Get total count for pagination
            total_count = query.count()

            # Apply pagination
            scores_with_accounts = query.offset(offset).limit(limit).all()

            # Pre-fetch comment stats if requested
            comment_stats_map = {}
            if include_comment_stats:
                account_ids = [account.id for score, account in scores_with_accounts]
                if account_ids:
                    stats = session.query(CommentStatsDB).filter(
                        CommentStatsDB.account_id.in_(account_ids)
                    ).all()
                    comment_stats_map = {s.account_id: s for s in stats}

            results = []
            for score, account in scores_with_accounts:
                result = {
                    "account": {
                        "id": account.id,
                        "username": account.username,
                        "display_name": account.display_name,
                        "platform": account.platform,
                        "created_at": account.created_at.isoformat() if account.created_at else None,
                        "follower_count": account.follower_count,
                        "post_count": account.post_count,
                        "metadata": account.platform_metadata
                    },
                    "score": {
                        "total_score": score.total_score,
                        "signals": score.signals,
                        "flagged": bool(score.flagged),
                        "last_updated": score.last_updated.isoformat() if score.last_updated else None
                    }
                }

                # Add comment stats if requested
                if include_comment_stats:
                    stats = comment_stats_map.get(account.id)
                    if stats:
                        result["comment_stats"] = {
                            "total_comments": stats.total_comments,
                            "inflammatory_count": stats.inflammatory_comment_count,
                            "inflammatory_ratio": stats.inflammatory_ratio,
                            "repetitive_count": stats.repetitive_comment_count
                        }
                    else:
                        result["comment_stats"] = None

                results.append(result)

            return {
                "accounts": results,
                "total": total_count,
                "limit": limit,
                "offset": offset
            }

    except Exception as e:
        logger.error(f"Error getting all accounts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{platform}/{account_id}")
async def get_account_detail(platform: str, account_id: str):
    """Get detailed information about a specific account."""
    try:
        db = get_database()

        with db.get_session() as session:
            # Get account
            account = session.query(AccountDB).filter_by(id=account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            # Get score
            score = session.query(ScoreDB).filter_by(account_id=account_id).first()

            # Get flags
            flags = session.query(FlagDB).filter_by(account_id=account_id).all()

            # Get recent posts
            posts = session.query(PostDB).filter_by(account_id=account_id)\
                .order_by(PostDB.created_at.desc()).limit(50).all()

            return {
                "account": {
                    "id": account.id,
                    "username": account.username,
                    "display_name": account.display_name,
                    "platform": account.platform,
                    "created_at": account.created_at.isoformat() if account.created_at else None,
                    "follower_count": account.follower_count,
                    "following_count": account.following_count,
                    "post_count": account.post_count,
                    "metadata": account.platform_metadata,  # Platform-specific attributes
                    "first_seen": account.first_seen.isoformat() if account.first_seen else None,
                    "last_analyzed": account.last_analyzed.isoformat() if account.last_analyzed else None
                },
                "score": {
                    "total_score": score.total_score,
                    "signals": score.signals,
                    "flagged": bool(score.flagged),
                    "threshold": score.threshold,
                    "last_updated": score.last_updated.isoformat() if score.last_updated else None
                } if score else None,
                "flags": [{
                    "flag_type": flag.flag_type,
                    "confidence_score": flag.confidence_score,
                    "reason": flag.reason,
                    "timestamp": flag.timestamp.isoformat() if flag.timestamp else None
                } for flag in flags],
                "recent_posts": [{
                    "id": post.id,
                    "content": post.content[:200] + "..." if len(post.content) > 200 else post.content,
                    "created_at": post.created_at.isoformat() if post.created_at else None,
                    "engagement": post.engagement
                } for post in posts]
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account detail: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts")
async def get_posts(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    flagged: bool = Query(False, description="Only show posts from flagged accounts"),
    limit: int = Query(50, ge=1, le=500, description="Maximum number of posts")
):
    """Get posts, optionally filtered."""
    try:
        db = get_database()

        with db.get_session() as session:
            query = session.query(PostDB)

            # Apply platform filter
            if platform:
                query = query.filter_by(platform=platform)

            # Apply flagged filter
            if flagged:
                flagged_account_ids = session.query(ScoreDB.account_id).filter_by(flagged=1).all()
                flagged_ids = [aid[0] for aid in flagged_account_ids]
                query = query.filter(PostDB.account_id.in_(flagged_ids))

            # Order by creation date and limit
            posts = query.order_by(PostDB.created_at.desc()).limit(limit).all()

            results = [{
                "id": post.id,
                "account_id": post.account_id,
                "platform": post.platform,
                "content": post.content[:300] + "..." if len(post.content) > 300 else post.content,
                "created_at": post.created_at.isoformat() if post.created_at else None,
                "engagement": post.engagement,
                "metadata": post.platform_metadata  # Platform-specific attributes
            } for post in posts]

            return {
                "posts": results,
                "total": len(results)
            }

    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/overview")
async def get_stats_overview(platform: Optional[str] = Query(None)):
    """Get overview statistics."""
    try:
        db = get_database()

        with db.get_session() as session:
            # Base queries
            accounts_query = session.query(AccountDB)
            posts_query = session.query(PostDB)
            scores_query = session.query(ScoreDB)

            # Apply platform filter if specified
            if platform:
                accounts_query = accounts_query.filter_by(platform=platform)
                posts_query = posts_query.filter_by(platform=platform)

            # Get counts
            total_accounts = accounts_query.count()
            total_posts = posts_query.count()
            flagged_accounts = scores_query.filter_by(flagged=1).count()
            total_flags = session.query(FlagDB).count()

            # Get platform breakdown
            platform_stats = {}
            for plat in ['bluesky', 'hackernews']:
                platform_stats[plat] = {
                    "accounts": session.query(AccountDB).filter_by(platform=plat).count(),
                    "posts": session.query(PostDB).filter_by(platform=plat).count()
                }

            return {
                "total_accounts": total_accounts,
                "total_posts": total_posts,
                "flagged_accounts": flagged_accounts,
                "total_flags": total_flags,
                "flag_rate": flagged_accounts / total_accounts if total_accounts > 0 else 0,
                "platform_breakdown": platform_stats
            }

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collection/trigger")
async def trigger_collection(
    platform: Optional[str] = Query(None, description="Specific platform to collect from"),
    query: Optional[str] = Query(None, description="Search query (hashtag, keyword, etc.)"),
    limit: int = Query(100, ge=1, le=10000, description="Maximum posts to collect"),
    harvest_comments: bool = Query(True, description="Harvest comments from top-performing posts")
):
    """Manually trigger a collection cycle with optional query."""
    try:
        collector = UniversalCollector()
        available_platforms = collector.get_available_platforms()

        if platform and platform not in available_platforms:
            raise HTTPException(status_code=400, detail=f"Platform not available: {platform}. Available: {available_platforms}")

        result = {
            "status": "success",
            "platform": platform,
            "query": query,
            "limit": limit,
            "posts_collected": 0,
            "accounts_discovered": 0,
            "comments_collected": 0,
            "timestamp": datetime.now().isoformat()
        }

        if query and platform:
            # Collect from specific platform with query
            posts = await collector.collect_from_platform(platform, query, limit)
            result["posts_collected"] = len(posts)

            # Count unique accounts
            account_ids = set(p.account_id for p in posts)
            result["accounts_discovered"] = len(account_ids)

            # Optionally harvest comments from top performers
            if harvest_comments and posts:
                # Identify top performers from collected posts
                top_posts = collector._identify_top_performers(posts)
                comments_count = 0
                if top_posts:
                    # Harvest comments from top performers
                    await collector._harvest_comments_phase(top_posts)
                    # Count comments collected in this batch
                    db = get_database()
                    with db.get_session() as session:
                        comments_count = session.query(PostDB).filter(
                            PostDB.parent_id.in_([p.id for p in top_posts]),
                            PostDB.post_type == 'comment'
                        ).count()
                result["comments_collected"] = comments_count
                result["message"] = f"Collected {len(posts)} posts from {len(account_ids)} accounts, harvested {comments_count} comments from {len(top_posts)} top posts"
            else:
                result["message"] = f"Collected {len(posts)} posts from {len(account_ids)} accounts"
        elif platform:
            # Run collection cycle for specific platform
            await collector.run_collection_cycle()
            result["message"] = f"Collection cycle completed for {platform}"
        else:
            # Trigger collection for all platforms
            await collector.run_collection_cycle()
            result["message"] = "Collection cycle completed for all platforms"

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering collection: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analysis/trigger")
async def trigger_analysis(
    account_id: Optional[str] = Query(None, description="Specific account to analyze"),
    platform: Optional[str] = Query(None, description="Analyze all accounts from platform")
):
    """Manually trigger bot detection analysis."""
    try:
        analyzer = BotDetector()

        if account_id:
            # Analyze specific account
            score = analyzer.analyze_account(account_id)
            if not score:
                raise HTTPException(status_code=404, detail="Account not found")

            return {
                "status": "success",
                "message": f"Analysis completed for account {account_id}",
                "score": {
                    "total_score": score.total_score,
                    "signals": score.signals,
                    "flagged": score.flagged
                }
            }
        else:
            # Analyze all accounts (optionally filtered by platform)
            scores = analyzer.analyze_all_accounts(platform=platform)

            return {
                "status": "success",
                "message": f"Analysis completed for {len(scores)} accounts",
                "total_analyzed": len(scores),
                "newly_flagged": sum(1 for s in scores if s.flagged)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Comment-related endpoints
# ============================================================================

@router.get("/comments/inflammatory")
async def get_inflammatory_comments(
    platform: Optional[str] = Query(None, description="Filter by platform"),
    min_severity: float = Query(0.3, ge=0.0, le=1.0, description="Minimum severity score"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Number of results to skip")
):
    """Get comments flagged as inflammatory."""
    try:
        db = get_database()

        with db.get_session() as session:
            query = session.query(InflammatoryFlagDB, PostDB, AccountDB).join(
                PostDB, InflammatoryFlagDB.post_id == PostDB.id
            ).join(
                AccountDB, InflammatoryFlagDB.account_id == AccountDB.id
            ).filter(
                InflammatoryFlagDB.severity_score >= min_severity
            )

            if platform:
                query = query.filter(InflammatoryFlagDB.platform == platform)

            # Get total count
            total_count = query.count()

            # Apply pagination and ordering
            results = query.order_by(
                InflammatoryFlagDB.severity_score.desc()
            ).offset(offset).limit(limit).all()

            return {
                "inflammatory_comments": [{
                    "flag": {
                        "id": flag.id,
                        "severity_score": flag.severity_score,
                        "toxicity_scores": flag.toxicity_scores,
                        "triggered_categories": flag.triggered_categories,
                        "content_snippet": flag.content_snippet,
                        "detected_at": flag.detected_at.isoformat() if flag.detected_at else None
                    },
                    "comment": {
                        "id": post.id,
                        "content": post.content[:300] if post.content else '',
                        "created_at": post.created_at.isoformat() if post.created_at else None,
                        "parent_id": post.parent_id
                    },
                    "account": {
                        "id": account.id,
                        "username": account.username,
                        "platform": account.platform
                    }
                } for flag, post, account in results],
                "total": total_count,
                "limit": limit,
                "offset": offset
            }

    except Exception as e:
        logger.error(f"Error getting inflammatory comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/posts/{platform}/{post_id}/comments")
async def get_post_comments(
    platform: str,
    post_id: str,
    include_inflammatory: bool = Query(True, description="Include inflammatory flags"),
    limit: int = Query(100, ge=1, le=500, description="Maximum comments")
):
    """Get comments for a specific post."""
    try:
        db = get_database()

        with db.get_session() as session:
            # Get the parent post
            parent_post = session.query(PostDB).filter_by(id=post_id).first()
            if not parent_post:
                raise HTTPException(status_code=404, detail="Post not found")

            # Get comments
            comments = session.query(PostDB).filter_by(
                parent_id=post_id
            ).order_by(PostDB.created_at.asc()).limit(limit).all()

            results = []
            for comment in comments:
                comment_data = {
                    "id": comment.id,
                    "account_id": comment.account_id,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "engagement": comment.engagement,
                    "post_type": comment.post_type
                }

                if include_inflammatory:
                    flag = session.query(InflammatoryFlagDB).filter_by(
                        post_id=comment.id
                    ).first()
                    if flag:
                        comment_data["inflammatory_flag"] = {
                            "severity": flag.severity_score,
                            "categories": flag.triggered_categories,
                            "toxicity_scores": flag.toxicity_scores
                        }

                results.append(comment_data)

            return {
                "parent_post": {
                    "id": parent_post.id,
                    "content": parent_post.content[:200] if parent_post.content else '',
                    "is_top_performer": bool(parent_post.is_top_performer),
                    "comments_collected": bool(parent_post.comments_collected),
                    "comments_collected_at": parent_post.comments_collected_at.isoformat() if parent_post.comments_collected_at else None
                },
                "comments": results,
                "total": len(results)
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting post comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{platform}/{account_id}/comment-stats")
async def get_account_comment_stats(platform: str, account_id: str):
    """Get comment behavior statistics for an account."""
    try:
        db = get_database()

        with db.get_session() as session:
            # Verify account exists
            account = session.query(AccountDB).filter_by(id=account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            stats = session.query(CommentStatsDB).filter_by(
                account_id=account_id
            ).first()

            if not stats:
                # Return empty stats if not yet computed
                return {
                    "account_id": account_id,
                    "platform": platform,
                    "comment_behavior": {
                        "total_comments": 0,
                        "total_original_posts": 0,
                        "comment_to_post_ratio": 0.0
                    },
                    "repetitiveness": {
                        "unique_comments": 0,
                        "repetitive_count": 0,
                        "repetitiveness_ratio": 0.0
                    },
                    "timing": {
                        "avg_seconds_between_comments": None,
                        "min_seconds_between_comments": None,
                        "rapid_fire_instances": 0
                    },
                    "inflammatory": {
                        "flagged_count": 0,
                        "inflammatory_ratio": 0.0
                    },
                    "engagement": {
                        "total_received": 0,
                        "average_per_comment": 0.0,
                        "comments_with_replies": 0
                    },
                    "last_updated": None
                }

            return {
                "account_id": account_id,
                "platform": stats.platform,
                "comment_behavior": {
                    "total_comments": stats.total_comments,
                    "total_original_posts": stats.total_original_posts,
                    "comment_to_post_ratio": stats.comment_to_post_ratio
                },
                "repetitiveness": {
                    "unique_comments": stats.unique_comment_hashes,
                    "repetitive_count": stats.repetitive_comment_count,
                    "repetitiveness_ratio": stats.repetitiveness_ratio
                },
                "timing": {
                    "avg_seconds_between_comments": stats.avg_seconds_between_comments,
                    "min_seconds_between_comments": stats.min_seconds_between_comments,
                    "rapid_fire_instances": stats.rapid_fire_instances
                },
                "inflammatory": {
                    "flagged_count": stats.inflammatory_comment_count,
                    "inflammatory_ratio": stats.inflammatory_ratio
                },
                "engagement": {
                    "total_received": stats.total_comment_engagement,
                    "average_per_comment": stats.avg_comment_engagement,
                    "comments_with_replies": stats.comments_with_replies
                },
                "last_updated": stats.last_updated.isoformat() if stats.last_updated else None
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting comment stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/accounts/{platform}/{account_id}/comments")
async def get_account_comments(
    platform: str,
    account_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    include_inflammatory_flags: bool = Query(True)
):
    """
    Get all comments made by a specific account.

    Useful for bot detection verification - allows reviewing all comments
    from an account to identify patterns like repetitive content, rapid-fire
    commenting, or coordinated behavior.
    """
    try:
        db = get_database()

        with db.get_session() as session:
            # Verify account exists
            account = session.query(AccountDB).filter_by(id=account_id).first()
            if not account:
                raise HTTPException(status_code=404, detail="Account not found")

            # Get all comments by this account
            comments_query = session.query(PostDB).filter(
                PostDB.account_id == account_id,
                PostDB.post_type == 'comment'
            ).order_by(PostDB.created_at.desc())

            total = comments_query.count()
            comments = comments_query.offset(offset).limit(limit).all()

            # Get inflammatory flags if requested
            inflammatory_map = {}
            if include_inflammatory_flags and comments:
                comment_ids = [c.id for c in comments]
                flags = session.query(InflammatoryFlagDB).filter(
                    InflammatoryFlagDB.post_id.in_(comment_ids)
                ).all()
                inflammatory_map = {f.post_id: f for f in flags}

            # Get parent post info for context
            parent_ids = list(set(c.parent_id for c in comments if c.parent_id))
            parent_posts = {}
            if parent_ids:
                parents = session.query(PostDB).filter(PostDB.id.in_(parent_ids)).all()
                parent_posts = {p.id: p for p in parents}

            result_comments = []
            for comment in comments:
                comment_data = {
                    "id": comment.id,
                    "content": comment.content,
                    "created_at": comment.created_at.isoformat() if comment.created_at else None,
                    "engagement": comment.engagement,
                    "parent_id": comment.parent_id,
                    "parent_preview": None,
                    "inflammatory": None
                }

                # Add parent post preview for context
                if comment.parent_id and comment.parent_id in parent_posts:
                    parent = parent_posts[comment.parent_id]
                    comment_data["parent_preview"] = {
                        "id": parent.id,
                        "content_snippet": parent.content[:200] if parent.content else None,
                        "account_id": parent.account_id
                    }

                # Add inflammatory flag if exists
                if comment.id in inflammatory_map:
                    flag = inflammatory_map[comment.id]
                    comment_data["inflammatory"] = {
                        "severity_score": flag.severity_score,
                        "triggered_categories": flag.triggered_categories,
                        "toxicity_scores": flag.toxicity_scores
                    }

                result_comments.append(comment_data)

            return {
                "account_id": account_id,
                "platform": platform,
                "username": account.username,
                "total_comments": total,
                "limit": limit,
                "offset": offset,
                "comments": result_comments
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting account comments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/comments")
async def get_comment_stats_overview(platform: Optional[str] = Query(None)):
    """Get overview statistics for comment collection and analysis."""
    try:
        db = get_database()

        with db.get_session() as session:
            # Base queries
            comments_query = session.query(PostDB).filter_by(post_type='comment')
            top_posts_query = session.query(PostDB).filter_by(is_top_performer=1)
            inflammatory_query = session.query(InflammatoryFlagDB)

            if platform:
                comments_query = comments_query.filter_by(platform=platform)
                top_posts_query = top_posts_query.filter_by(platform=platform)
                inflammatory_query = inflammatory_query.filter_by(platform=platform)

            # Get counts
            total_comments = comments_query.count()
            top_performing_posts = top_posts_query.count()
            posts_with_comments = session.query(PostDB).filter(
                PostDB.comments_collected == 1
            ).count()
            inflammatory_flags = inflammatory_query.count()

            # Get unique accounts flagged
            unique_flagged = session.query(
                func.count(func.distinct(InflammatoryFlagDB.account_id))
            ).scalar() or 0

            # Get average severity
            avg_severity = session.query(
                func.avg(InflammatoryFlagDB.severity_score)
            ).scalar() or 0.0

            # Get category breakdown
            category_counts = {}
            all_flags = inflammatory_query.all()
            for flag in all_flags:
                for cat in (flag.triggered_categories or []):
                    category_counts[cat] = category_counts.get(cat, 0) + 1

            return {
                "total_comments_collected": total_comments,
                "top_performing_posts": top_performing_posts,
                "posts_with_comments_harvested": posts_with_comments,
                "inflammatory_flags": inflammatory_flags,
                "unique_accounts_flagged": unique_flagged,
                "avg_severity": round(avg_severity, 3),
                "category_breakdown": category_counts
            }

    except Exception as e:
        logger.error(f"Error getting comment stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))
