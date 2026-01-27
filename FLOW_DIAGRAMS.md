# Purisa Bot Detection System - Flow Diagrams

Technical documentation for the collection and analysis pipelines.

---

## Collection Flow

How posts and comments are collected from social media platforms.

```mermaid
flowchart TD
    subgraph Trigger["1. TRIGGER"]
        API["POST /api/collection/trigger"]
        CLI["CLI: purisa collect --query"]
    end

    subgraph Init["2. INITIALIZATION"]
        UC["UniversalCollector()"]
        CFG["Load platforms.yaml config"]
        PLAT["Initialize Platform Adapters<br/>(Bluesky, HackerNews)"]
    end

    subgraph Collect["3. POST COLLECTION"]
        FETCH["platform.collect_posts(query, limit)"]
        TRANSFORM["Transform to generic Post model"]
        STORE_POST["Store in PostDB"]
        STORE_ACCT["Create/Update AccountDB"]
    end

    subgraph TopPerf["4. TOP PERFORMER IDENTIFICATION"]
        CALC_ENG["Calculate engagement score<br/>(likes + reposts×2 + replies×1.5) / 1000"]
        FILTER["Filter: score ≥ min_engagement_score"]
        CAP["Cap at max_posts_for_comment_harvest"]
        MARK["Mark PostDB.is_top_performer = 1"]
    end

    subgraph Comments["5. COMMENT HARVESTING"]
        FETCH_COMMENTS["platform.get_post_comments()"]
        STORE_COMMENTS["Store comments in PostDB<br/>post_type='comment', parent_id=post.id"]
        FETCH_PROFILES["Batch fetch full profiles<br/>for new commenter accounts"]
        MARK_COLLECTED["Mark PostDB.comments_collected = 1"]
    end

    subgraph Inflammatory["6. INFLAMMATORY DETECTION"]
        DETOXIFY["Detoxify ML Model<br/>analyze_batch(comment_texts)"]
        FLAG["Create InflammatoryFlagDB<br/>severity_score, triggered_categories"]
        QUEUE["Queue account for analysis"]
    end

    subgraph Output["7. OUTPUT"]
        RESULT["Return: posts_collected,<br/>accounts_discovered,<br/>comments_collected"]
    end

    API --> UC
    CLI --> UC
    UC --> CFG --> PLAT
    PLAT --> FETCH --> TRANSFORM
    TRANSFORM --> STORE_POST --> STORE_ACCT
    STORE_ACCT --> CALC_ENG --> FILTER --> CAP --> MARK
    MARK --> FETCH_COMMENTS --> STORE_COMMENTS --> FETCH_PROFILES --> MARK_COLLECTED
    MARK_COLLECTED --> DETOXIFY --> FLAG --> QUEUE
    QUEUE --> RESULT
```

### Key Files - Collection

| Component | File | Lines |
|-----------|------|-------|
| API Endpoint | `backend/purisa/api/routes.py` | 372-441 |
| Collector Service | `backend/purisa/services/collector.py` | 23-560 |
| Batch Profile Fetch | `backend/purisa/services/collector.py` | 464-511 |
| Bluesky Adapter | `backend/purisa/platforms/bluesky.py` | 68-270 |
| Inflammatory Detector | `backend/purisa/services/inflammatory.py` | 26-182 |
| Database Models | `backend/purisa/database/models.py` | 17-183 |

### Configuration Parameters (Comment Harvesting)

The relationship between collection parameters and comment harvesting:

```
limit (API/CLI parameter)
    │
    ▼
┌──────────────────────────────────────┐
│ Collect N posts from platform        │
│ (controlled by 'limit' parameter)    │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Filter by engagement score           │
│ (min_engagement_score threshold)     │
│                                      │
│ Example: 100 posts → 40 qualify      │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Cap at max_posts_for_comment_harvest │
│                                      │
│ Example: 40 qualifying → 50 cap      │
│          = 40 selected (no capping)  │
│                                      │
│ Example: 60 qualifying → 50 cap      │
│          = 50 selected (10 skipped)  │
└──────────────────────────────────────┘
    │
    ▼
┌──────────────────────────────────────┐
│ Harvest comments from selected posts │
│ (max_comments_per_post per post)     │
└──────────────────────────────────────┘
```

| Parameter | Default | Location | Purpose |
|-----------|---------|----------|---------|
| `limit` | 100 | API/CLI | Max posts to collect initially |
| `min_engagement_score` | 0.01 | platforms.yaml | Threshold for "top performer" |
| `max_posts_for_comment_harvest` | 50 | platforms.yaml | Cap on posts to harvest comments from |
| `max_comments_per_post` | 100 | platforms.yaml | Max comments per top post |
| `fetch_commenter_profiles` | true | platforms.yaml | Fetch full profiles for commenters |

**Best Practice:** Set `limit >= 2 * max_posts_for_comment_harvest` to ensure enough posts qualify.

---

## Analysis Flow

How bot detection scoring works using 13 behavioral signals.

```mermaid
flowchart TD
    subgraph Trigger["1. TRIGGER"]
        API["POST /api/analysis/trigger"]
        CLI["CLI: purisa analyze"]
        AUTO["Auto: After inflammatory detection"]
    end

    subgraph Load["2. LOAD DATA"]
        ACCT["Query AccountDB"]
        POSTS["Query PostDB for account"]
        SPLIT["Split: original_posts vs comments"]
    end

    subgraph Original["3. ORIGINAL 8 SIGNALS"]
        S1["new_account (0-2.0)<br/>Account age check"]
        S2["high_frequency (0-3.0)<br/>Posts per 24 hours"]
        S3["repetitive_content (0-2.5)<br/>Jaccard similarity >70%"]
        S4["low_engagement (0-1.5)<br/>Avg engagement per post"]
        S5["generic_username (0-1.0)<br/>Regex patterns"]
        S6["incomplete_profile (0-1.0)<br/>Missing bio/avatar"]
        S7["temporal_pattern (0-1.0)<br/>24/7 posting activity"]
        S8["unverified_account (0-1.5)<br/>Verification status"]
    end

    subgraph Comment["4. COMMENT 5 SIGNALS"]
        S9["comment_repetitiveness (0-2.0)<br/>Duplicate comments >70% similar"]
        S10["comment_timing (0-2.5)<br/>Rapid-fire <30s apart"]
        S11["inflammatory_frequency (0-2.0)<br/>% comments flagged toxic"]
        S12["comment_to_post_ratio (0-1.5)<br/>Only comments, never posts"]
        S13["comment_engagement (0-1.5)<br/>Zero engagement on comments"]
    end

    subgraph Score["5. SCORING"]
        SUM["total_score = sum(13 signals)<br/>Max: 22.0"]
        THRESHOLD["flagged = (score ≥ 7.0)"]
    end

    subgraph Store["6. STORAGE"]
        SCORE_DB["ScoreDB<br/>total_score, signals, flagged"]
        STATS_DB["CommentStatsDB<br/>Aggregated comment metrics"]
        FLAG_DB["FlagDB<br/>Significant signals ≥1.0"]
        UPDATE_ACCT["AccountDB.last_analyzed"]
    end

    subgraph Output["7. OUTPUT"]
        RESULT["Return: Score object<br/>total_score, signals, flagged"]
    end

    API --> ACCT
    CLI --> ACCT
    AUTO --> ACCT
    ACCT --> POSTS --> SPLIT

    SPLIT --> S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8
    SPLIT --> S9 & S10 & S11 & S12 & S13

    S1 & S2 & S3 & S4 & S5 & S6 & S7 & S8 --> SUM
    S9 & S10 & S11 & S12 & S13 --> SUM

    SUM --> THRESHOLD
    THRESHOLD --> SCORE_DB & STATS_DB & FLAG_DB & UPDATE_ACCT
    SCORE_DB --> RESULT
```

### Key Files - Analysis

| Component | File | Lines |
|-----------|------|-------|
| API Endpoint | `backend/purisa/api/routes.py` | 444-483 |
| Analyzer Service | `backend/purisa/services/analyzer.py` | 23-795 |
| Original Signals | `backend/purisa/services/analyzer.py` | 416-682 |
| Comment Signals | `backend/purisa/services/analyzer.py` | 96-334 |
| Score Storage | `backend/purisa/services/analyzer.py` | 684-734 |
| Database Models | `backend/purisa/database/models.py` | 134-230 |

---

## Signal Reference

### Original Signals (Profile & Post Behavior)

| # | Signal | Max | Detection Method |
|---|--------|-----|------------------|
| 1 | new_account | 2.0 | Account age < 30 days |
| 2 | high_frequency | 3.0 | >24 posts in 24 hours |
| 3 | repetitive_content | 2.5 | Jaccard similarity >70% across posts |
| 4 | low_engagement | 1.5 | Avg likes+reposts+replies < threshold |
| 5 | generic_username | 1.0 | Matches patterns: user123, bot_, etc. |
| 6 | incomplete_profile | 1.0 | Missing description or avatar |
| 7 | temporal_pattern | 1.0 | Posts across >20 unique hours (24/7 activity) |
| 8 | unverified_account | 1.5 | No verification badge |

### Comment Signals (Comment Behavior)

| # | Signal | Max | Detection Method |
|---|--------|-----|------------------|
| 9 | comment_repetitiveness | 2.0 | >30% duplicate/similar comments |
| 10 | comment_timing | 2.5 | >30% comments posted <30 seconds apart |
| 11 | inflammatory_frequency | 2.0 | >30% comments flagged toxic by Detoxify ML |
| 12 | comment_to_post_ratio | 1.5 | Account only comments, never creates posts |
| 13 | comment_engagement | 1.5 | Avg engagement <0.5 per comment |

### Scoring

- **Maximum Total Score:** 22.0
- **Flag Threshold:** 7.0 (accounts scoring ≥7.0 are flagged as suspicious)

---

## Database Schema

```
┌─────────────┐     ┌─────────────┐     ┌─────────────────────┐
│  AccountDB  │────<│   PostDB    │────<│ InflammatoryFlagDB  │
│             │     │             │     │                     │
│ id          │     │ id          │     │ post_id (FK)        │
│ username    │     │ account_id  │     │ account_id (FK)     │
│ platform    │     │ content     │     │ severity_score      │
│ follower_ct │     │ post_type   │     │ toxicity_scores     │
│ last_analyzed│    │ parent_id   │     │ triggered_categories│
└─────────────┘     │ is_top_perf │     └─────────────────────┘
       │            └─────────────┘
       │
       ▼
┌─────────────┐     ┌─────────────────┐
│   ScoreDB   │     │ CommentStatsDB  │
│             │     │                 │
│ account_id  │     │ account_id      │
│ total_score │     │ total_comments  │
│ signals     │     │ inflammatory_ct │
│ flagged     │     │ repetitive_ct   │
│ threshold   │     │ rapid_fire_ct   │
└─────────────┘     └─────────────────┘
```

### Table Descriptions

| Table | Purpose |
|-------|---------|
| **AccountDB** | User profiles from social platforms |
| **PostDB** | Original posts and comments (post_type field distinguishes) |
| **ScoreDB** | Bot detection scores and all 13 signal values |
| **InflammatoryFlagDB** | Individual toxic comment flags with ML scores |
| **CommentStatsDB** | Aggregated per-account comment statistics |

---

## API Endpoints

### Collection

```
POST /api/collection/trigger
  ?platform=bluesky
  &query=#politics
  &limit=50
  &harvest_comments=true
```

### Analysis

```
POST /api/analysis/trigger
  ?account_id=<id>     # Single account
  ?platform=bluesky    # All accounts on platform
```

### Results

```
GET /api/accounts/flagged              # Flagged accounts
GET /api/accounts/{platform}/{id}/comments  # Account's comments
GET /api/comments/inflammatory         # All toxic comments
GET /api/stats/overview               # System statistics
```
