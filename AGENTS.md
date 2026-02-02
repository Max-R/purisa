# Purisa Development Progress

## Project Overview
Multi-platform social media coordination detection system. Analyzes Bluesky (primary) and Hacker News (secondary) for coordinated inauthentic behavior patterns using network analysis.

**Current Version**: 2.0.0 (Coordination Detection)

## Current Phase: Phase 2 Complete (Coordination Detection)

### Completed ✅

#### Backend Infrastructure
- [x] Project structure setup (backend/frontend)
- [x] Backend Python package structure with all modules
- [x] SQLite database models and schema
- [x] Database connection and initialization
- [x] Pydantic configuration settings with environment variables
- [x] Platform configuration YAML file
- [x] FastAPI application with CORS
- [x] Comprehensive logging setup

#### Platform Adapters
- [x] Abstract SocialPlatform base class
  - [x] `get_post_comments()` abstract method
  - [x] `get_engagement_score()` abstract method
- [x] Bluesky platform adapter using atproto library
  - [x] Post collection (search/hashtags)
  - [x] Account information retrieval
  - [x] Account posting history
  - [x] Proper timestamp parsing
  - [x] Engagement metrics mapping
  - [x] Comment/reply harvesting via `app.bsky.feed.get_post_thread`
  - [x] Normalized engagement scoring
- [x] Hacker News platform adapter using httpx
  - [x] Top/new/best stories collection
  - [x] User information retrieval
  - [x] Submission history
  - [x] No authentication required
  - [x] Karma and engagement mapping
  - [x] Recursive comment fetching via Firebase API
  - [x] Normalized engagement scoring

#### Data Models
- [x] Pydantic models (Account, Post, Flag, Score)
- [x] SQLAlchemy database models
  - [x] PostDB with comment support (parent_id, post_type, is_top_performer)
  - [x] InflammatoryFlagDB for tracking toxic comments
  - [x] CommentStatsDB for aggregated comment statistics
- [x] Platform-agnostic data structures
- [x] Proper indexes for performance

#### Coordination Detection (NEW in 2.0)
- [x] New database tables for coordination detection:
  - [x] AccountEdgeDB - Pairwise account similarity edges
  - [x] CoordinationClusterDB - Detected coordination clusters
  - [x] ClusterMemberDB - Cluster membership with centrality scores
  - [x] CoordinationMetricDB - Hourly/daily coordination metrics
  - [x] EventDB - User-contributed or auto-detected events
  - [x] EventCorrelationDB - Link coordination spikes to events
- [x] CoordinationAnalyzer service (`coordination.py`)
  - [x] Build similarity networks with NetworkX
  - [x] Synchronized posting detection (90-second window)
  - [x] URL sharing detection
  - [x] Text similarity with TF-IDF (>0.8 threshold)
  - [x] Hashtag overlap detection
  - [x] Reply pattern detection
  - [x] Louvain community detection for clusters
  - [x] Hourly coordination scoring (0-100)
  - [x] Historical metrics storage
  - [x] Spike detection (z-score based)
- [x] TextSimilarityCalculator service (`similarity.py`)
  - [x] TF-IDF vectorization with scikit-learn
  - [x] Cosine similarity calculation
  - [x] URL extraction and matching
  - [x] Hashtag overlap calculation

#### Services
- [x] UniversalCollector service
  - [x] Platform-agnostic collection
  - [x] Automatic account discovery
  - [x] Post storage with deduplication
  - [x] YAML configuration loading
  - [x] Environment variable substitution
  - [x] Top performer identification (engagement-based)
  - [x] Comment harvesting from top posts
  - [x] Inflammatory content analysis integration
  - [x] Account flagging for bot analysis
  - [x] Full profile fetch for commenter accounts (batch, with progress logging)
- [x] BotDetector analyzer with 13 detection signals (legacy, kept for reference)
- [x] Inflammatory content detector (Detoxify ML)
  - [x] Lazy loading for performance
  - [x] Batch inference support
  - [x] 6 toxicity categories
  - [x] Configurable threshold (default 0.5)
- [x] BackgroundScheduler with APScheduler
  - [x] Configurable collection intervals
  - [x] Automatic analysis scheduling
  - [x] Error handling and logging

#### API Endpoints
- [x] GET /api/health - Health check
- [x] GET /api/platforms/status - Platform availability
- [x] GET /api/accounts/all - List all accounts (paginated)
- [x] GET /api/accounts/{platform}/{id} - Account details
- [x] GET /api/posts - Get posts with filters
- [x] GET /api/stats/overview - Statistics overview
- [x] POST /api/collection/trigger - Manual collection trigger
- [x] POST /api/analysis/trigger - Manual analysis trigger
- [x] **NEW** GET /api/coordination/metrics - Get coordination metrics
- [x] **NEW** GET /api/coordination/spikes - Get coordination spikes
- [x] **NEW** GET /api/coordination/timeline - Get coordination timeline
- [x] **NEW** GET /api/coordination/clusters - Get detected clusters
- [x] **NEW** POST /api/coordination/analyze - Trigger coordination analysis
- [x] **NEW** GET /api/coordination/stats - Get coordination statistics

#### Frontend
- [x] Bun native tooling (no Vite) + React 19 setup
- [x] TypeScript configuration with JSX support
- [x] TailwindCSS styling with CSS variables for theming
- [x] PostCSS and Autoprefixer
- [x] shadcn/ui component library (Radix UI primitives)
- [x] Dark mode support
- [x] TypeScript types (Account, Post, Detection, Stats, CommentStats)
- [x] API client with Axios
- [x] React hooks for state management
- [x] Dashboard with tab navigation
- [x] StatsCards component
- [x] AccountsTable component (legacy)
- [x] PlatformFilter component
- [x] CollectionPanel component for UI-based data collection
- [x] Responsive design
- [x] Loading and error states
- [x] Hot Module Replacement (HMR) via Bun native

#### CLI Tool
- [x] init command - Database initialization
- [x] collect command - Data collection
  - [x] Multi-query support (can specify --query multiple times)
  - [x] Platform-specific collection
  - [x] Batch processing with progress output
  - [x] Progress bars (tqdm)
  - [x] `--harvest-comments / --no-harvest-comments` flag
  - [x] Top performer stats display
- [x] **REWRITTEN** analyze command - Coordination detection
  - [x] `--platform` option for platform selection
  - [x] `--hours` option for analysis window
  - [x] `--start` option for start time
  - [x] Progress bar for hourly analysis
  - [x] Summary output with high coordination hours
- [x] **NEW** spikes command - Spike detection
  - [x] `--platform` option
  - [x] `--hours` option for lookback period
  - [x] `--threshold` option for sensitivity
  - [x] Table output with z-scores
- [x] stats command - Show statistics (updated for coordination)
- [x] Tabulate formatting for output
- [x] Platform filtering
- [x] Error handling
- [x] Install script for system-wide `purisa` command
- [x] .env loading fix for backend credentials

#### Documentation
- [x] Comprehensive README.md
- [x] CLI_MANUAL.md - Complete CLI reference (updated for 2.0)
- [x] AGENTS.md (this file)
- [x] .env.example with all variables
- [x] Code comments and docstrings
- [x] Type hints throughout

#### Configuration
- [x] .gitignore for Python and Node/Bun
- [x] requirements.txt (including networkx, scikit-learn, pandas)
- [x] setup.py for backend package
- [x] package.json for frontend
- [x] Platform configuration YAML
- [x] Environment variable system
- [x] start.sh - Automated startup script
- [x] stop.sh - Graceful shutdown script
- [x] install.sh - CLI installation script

### In Progress 🚧

- [ ] Frontend dashboard redesign for coordination timeline view
- [ ] Coordination visualization components

### Blocked ⛔

None

## Testing Status

### Manual Testing Completed
- [x] Database initialization
- [x] Platform adapters (Bluesky, HN)
- [x] Data collection workflow
- [x] Coordination analysis algorithm
- [x] Cluster detection with real data
- [x] Spike detection
- [x] Historical metrics storage
- [x] API endpoints
- [x] CLI commands

### Test Results (2026-02-01)
- **HackerNews**: 49 posts, 2071 comments - no coordination detected (expected for organic data)
- **Bluesky**: 88 posts - 9 clusters detected, 2 spikes (100.0 score)
- **Metrics stored**: All hours in analysis window, including zero-activity hours

### Automated Testing
- [ ] Unit tests for coordination detection
- [ ] Unit tests for similarity calculation
- [ ] Integration tests for API
- [ ] End-to-end tests for workflow

## Future Phases

### Phase 3: Dashboard Redesign

**Goal**: Replace account-based dashboard with coordination timeline view

- [ ] Coordination timeline chart component
- [ ] Spike detail view
- [ ] Remove individual account scoring view
- [ ] Add cluster visualization
- [ ] Add event correlation UI

### Phase 4: Event Correlation

**Goal**: Add event tracking and correlation

- [ ] Event entry UI
- [ ] Event overlay on timeline
- [ ] Correlation analysis (pre/post event patterns)
- [ ] Spike alerting

### Phase 5: Multi-Platform Expansion

**Goal**: Add more social media platforms

- [ ] Mastodon integration
- [ ] Twitter/X integration (if access available)
- [ ] Reddit integration (if access available)
- [ ] Cross-platform coordination detection

### Phase 6: Production Ready

**Goal**: Deploy to production with enterprise features

- [ ] PostgreSQL migration
- [ ] Docker containerization
- [ ] Cloud deployment
- [ ] Authentication system
- [ ] API rate limiting
- [ ] Caching layer
- [ ] Automated testing suite
- [ ] CI/CD pipeline

## Technical Decisions Log

### 2026-01-23 - Initial Architecture

**Decision**: Start with Bluesky instead of Reddit
**Rationale**: Reddit API severely restricted after mid-2023; Bluesky has open API with no application process
**Impact**: Faster development start, no API approval delays

**Decision**: Add Hacker News as secondary platform
**Rationale**: Completely open API, no auth required, good for testing architecture
**Impact**: Can validate multi-platform design immediately without complex auth

**Decision**: Platform adapter pattern with native libraries
**Rationale**: Best of both worlds - abstraction for extensibility + full platform features
**Impact**: Extensible architecture, full API access, easy to add platforms

**Decision**: Use SQLite for initial development
**Rationale**: Zero-config, easy migration path to PostgreSQL
**Impact**: Faster initial development, schema flexibility, simple deployment

### 2026-01-24 - Vue→React Migration

**Decision**: Migrate from Vue 3 to React 19 with Bun native tooling
**Rationale**: Bun 1.3+ provides native frontend dev server with HMR; eliminates Vite dependency
**Impact**: Removed Vite, vue-router, Pinia; replaced with React, React Router 7, custom hooks

### 2026-01-24 - Comment-Based Bot Detection

**Decision**: Add 5 comment-based detection signals (total 13 signals, max 22.0 points)
**Rationale**: Research shows bots operate as "amplification parasites" targeting comment sections
**Impact**: Better detection of comment-spamming bots

**Decision**: Use Detoxify ML library for inflammatory detection
**Rationale**: Local ML model (98%+ AUC) without external API dependencies
**Impact**: Fast, accurate toxicity detection without API costs

### 2026-02-01 - Purisa 2.0 Coordination Detection

**Decision**: Shift from individual account scoring to network-based coordination detection
**Rationale**: Network analysis detects coordinated behavior more effectively than individual signals; avoids false positive issues with individual account flagging; focuses on patterns rather than individuals
**Impact**: Complete paradigm shift - new database tables, services, CLI commands, and API endpoints

**Decision**: Use NetworkX for in-memory graph analysis
**Rationale**: Zero infrastructure (no Neo4j needed); Python-native; great for batch analysis; easy migration path to graph DB later if needed for scale
**Impact**: Simple deployment, no external dependencies, sufficient for local/MVP use

**Decision**: Use TF-IDF for text similarity over sentence embeddings
**Rationale**: Faster, simpler, sufficient for MVP; sentence embeddings (BERT/etc) add complexity and compute requirements without proven benefit for this use case
**Impact**: Faster analysis, lower resource requirements, scikit-learn dependency only

**Decision**: 90-second window for synchronized posting detection
**Rationale**: Start inclusive to catch coordination; can tighten threshold if false positives are high
**Impact**: Configurable via CoordinationConfig dataclass

**Decision**: Louvain community detection for cluster identification
**Rationale**: Well-established algorithm, good balance of speed and accuracy, available in NetworkX
**Impact**: Reliable cluster detection with configurable resolution parameter

**Decision**: Store metrics for all analyzed hours (including zero-activity)
**Rationale**: Historical tracking requires consistent time series; gaps in data make trend analysis difficult
**Impact**: Complete historical record for baseline calculation and trend analysis

**Decision**: Use time_window_start for cluster_id instead of datetime.now()
**Rationale**: Enables idempotent re-analysis; prevents UNIQUE constraint errors when re-running
**Impact**: Can safely re-run analysis on same time window

## Known Issues

### Recently Fixed ✅
- ✅ Timestamp precision handling (atproto 0.0.65 nanosecond support)
- ✅ Snake_case to camelCase type mismatches in frontend
- ✅ SQLAlchemy `metadata` reserved name (renamed to cluster_metadata, etc.)
- ✅ cluster_id using datetime.now() instead of time window (fixed for idempotent re-analysis)
- ✅ Metrics not stored for zero-activity hours (now stored for all analyzed hours)
- ✅ CLI not loading backend/.env for platform credentials (added dotenv loading)

### Minor Issues
- Bluesky account creation date not directly exposed in API (workaround: using current time)
- HN Firebase API doesn't support keyword search (would need Algolia integration)
- Some npm audit warnings (moderate severity)

### Performance Considerations
- SQLite may struggle with >100k accounts (migration to PostgreSQL recommended)
- NetworkX builds graphs in-memory (may need optimization for very large datasets)
- Pagination added to frontend tables with configurable page sizes

### Security Considerations
- No authentication on API (intentional for MVP, but needed for production)
- Bluesky credentials in plaintext .env file (acceptable for local dev only)
- CORS allows all origins in dev mode (needs restriction for production)

## Performance Metrics

_From testing on 2026-02-01_

- Posts collected (Bluesky): 88
- Posts collected (HN): 2140 (49 posts + 2071 comments)
- Clusters detected (Bluesky): 9
- Coordination spikes found: 2
- Analysis time (6 hours): ~0.06 seconds
- Database size: ~5MB

## Notes for Future Development

### Coordination Detection Improvements

**High Priority:**
- Add topic extraction (keyword/hashtag clustering) for coordinated content
- Implement cross-platform coordination detection
- Add network visualization (D3.js force-directed graph)
- Implement real-time streaming analysis

**Medium Priority:**
- Add more coordination signals (follower overlap, timing patterns)
- Implement alert system for high-coordination spikes
- Add export functionality for coordination reports
- Consider graph database (Neo4j) for scale

**Low Priority:**
- Add machine learning classification of coordination types
- Implement historical comparison (this week vs last week)
- Add geographic analysis (if location data available)

### Architecture Improvements

**Database:**
- Add Redis for caching frequently accessed metrics
- Implement database connection pooling for PostgreSQL
- Consider time-series database for high-frequency analysis (TimescaleDB)

**API:**
- Add WebSocket support for real-time updates
- Implement batch operations for bulk analysis
- Add GraphQL endpoint for flexible queries

**Frontend:**
- Add real-time updates using WebSockets
- Implement coordination timeline visualization
- Add drill-down from spike to cluster details

## Success Metrics for 2.0

- [x] Successfully detect coordination in test data
- [x] Spike detection identifies unusual activity
- [x] Historical metrics stored for all analyzed hours
- [x] CLI commands work end-to-end
- [x] API endpoints return correct data
- [ ] Dashboard shows coordination timeline (pending frontend update)
- [ ] False positive rate < 20% on manual review (pending validation)

## Resources & References

**Documentation:**
- Bluesky AT Protocol: https://atproto.com/
- Hacker News API: https://github.com/HackerNews/API
- FastAPI: https://fastapi.tiangolo.com/
- NetworkX: https://networkx.org/
- scikit-learn TF-IDF: https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
- Louvain Algorithm: https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.community.louvain.louvain_communities.html

**Research:**
- Coordinated Inauthentic Behavior detection
- Social network analysis for bot detection
- Community detection algorithms

## Contributors

- Initial development: Purisa Team
- See GitHub for contributor list

---

Last Updated: 2026-02-01
Version: 2.0.0 (Coordination Detection)
