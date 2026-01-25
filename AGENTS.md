# Purisa Development Progress

## Project Overview
Multi-platform social media bot detection system. Starting with Bluesky (primary) and Hacker News (secondary), with plans to expand to Mastodon, Twitter/X, and Reddit.

**Current Version**: 0.6.0 (Collection Panel UI)

## Current Phase: MVP (Phase 1)

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
- [x] BotDetector analyzer with 13 detection signals:
  - [x] New account detection (0-2 points)
  - [x] High frequency posting (0-3 points)
  - [x] Repetitive content (0-2.5 points)
  - [x] Low engagement ratio (0-1.5 points)
  - [x] Generic username patterns (0-1 point)
  - [x] Incomplete profile (0-1 point)
  - [x] Temporal posting patterns (0-1 point)
  - [x] Unverified account/trust signals (0-1.5 points)
  - [x] Comment repetitiveness (0-2 points)
  - [x] Comment timing / rapid-fire (0-2.5 points)
  - [x] Inflammatory frequency (0-2 points)
  - [x] Comment-to-post ratio (0-1.5 points)
  - [x] Comment engagement ratio (0-1.5 points)
- [x] Inflammatory content detector (Detoxify ML)
  - [x] Lazy loading for performance
  - [x] Batch inference support
  - [x] 6 toxicity categories (toxic, severe_toxic, obscene, threat, insult, identity_hate)
  - [x] Configurable threshold (default 0.5)
- [x] BackgroundScheduler with APScheduler
  - [x] Configurable collection intervals
  - [x] Automatic analysis scheduling
  - [x] Error handling and logging

#### API Endpoints
- [x] GET /api/health - Health check
- [x] GET /api/platforms/status - Platform availability
- [x] GET /api/accounts/all - List all accounts with scores (paginated, limit up to 5000)
- [x] GET /api/accounts/flagged - List flagged accounts (paginated, limit up to 5000)
- [x] GET /api/accounts/{platform}/{id} - Account details
- [x] GET /api/accounts/{platform}/{id}/comment-stats - Account comment behavior stats
- [x] GET /api/posts - Get posts with filters
- [x] GET /api/posts/{platform}/{id}/comments - Get comments for a post
- [x] GET /api/comments/inflammatory - List inflammatory comments with filters
- [x] GET /api/stats/overview - Statistics overview
- [x] GET /api/stats/comments - Comment collection statistics
- [x] POST /api/collection/trigger - Manual collection trigger
- [x] POST /api/analysis/trigger - Manual analysis trigger
- [x] Snake_case to camelCase transformation in API client

#### Frontend
- [x] Bun native tooling (no Vite) + React 19 setup
- [x] TypeScript configuration with JSX support
- [x] TailwindCSS styling with CSS variables for theming
- [x] PostCSS and Autoprefixer
- [x] shadcn/ui component library (Radix UI primitives)
  - [x] Button, Card, Badge, Table, Tabs, Select components
  - [x] Skeleton loading states
  - [x] class-variance-authority for variants
- [x] Dark mode support
  - [x] ThemeContext with React Context API
  - [x] ThemeToggle component (Sun/Moon icons)
  - [x] localStorage persistence
  - [x] System preference detection
- [x] TypeScript types (Account, Post, Detection, Stats, CommentStats)
- [x] API client with Axios
- [x] Data transformation layer (snake_case → camelCase)
- [x] React hooks for state management (useStats, useAccounts, usePlatforms)
- [x] Dashboard with tab navigation
  - [x] "All Accounts" view (shows all analyzed accounts)
  - [x] "Flagged Accounts" view (shows only suspicious accounts)
- [x] StatsCards component with 7 metrics (4 core + 3 comment stats)
- [x] AccountsTable component with scoring visualization
- [x] PlatformFilter component
- [x] CollectionPanel component for UI-based data collection
  - [x] Platform selection dropdown
  - [x] Search query input with placeholder hints
  - [x] Configurable post limit (50-5000)
  - [x] Comment harvesting toggle
  - [x] Collect Only / Analyze Only / Collect & Analyze buttons
  - [x] Real-time progress feedback and results display
- [x] Responsive design
- [x] Loading and error states
- [x] Hot Module Replacement (HMR) via Bun native

#### CLI Tool
- [x] init command - Database initialization
- [x] collect command - Data collection
  - [x] Multi-query support (can specify --query multiple times)
  - [x] Platform-specific collection
  - [x] Batch processing with progress output
- [x] analyze command - Bot detection
- [x] flagged command - View flagged accounts
- [x] stats command - Show statistics
- [x] Tabulate formatting for output
- [x] Platform filtering
- [x] Error handling
- [x] Install script for system-wide `purisa` command

#### Documentation
- [x] Comprehensive README.md
  - [x] Quick start guide with ./start.sh
  - [x] In-depth detection signals documentation
  - [x] Platform-specific differences
  - [x] API documentation
  - [x] Configuration guide
  - [x] Troubleshooting section
  - [x] Example bot scores and explanations
- [x] CLI_MANUAL.md - Complete CLI reference
  - [x] All commands documented
  - [x] Multi-query examples
  - [x] Workflow guides
  - [x] Best practices
- [x] AGENTS.md (this file)
- [x] .env.example with all variables
- [x] Code comments and docstrings
- [x] Type hints throughout

#### Configuration
- [x] .gitignore for Python and Node/Bun
- [x] requirements.txt (latest versions, including detoxify>=0.5.2)
- [x] setup.py for backend package
- [x] package.json for frontend
- [x] Platform configuration YAML
- [x] Environment variable system
- [x] start.sh - Automated startup script
- [x] stop.sh - Graceful shutdown script
- [x] install.sh - CLI installation script

### In Progress 🚧

None currently - MVP is complete!

### Blocked ⛔

None

## Testing Status

### Manual Testing Completed
- [x] Database initialization
- [x] Platform adapters (Bluesky, HN)
- [x] Data collection workflow
- [x] Bot detection algorithm
- [x] API endpoints
- [x] Frontend components
- [x] CLI commands

### Automated Testing
- [ ] Unit tests for platform adapters
- [ ] Unit tests for detection signals
- [ ] Integration tests for API
- [ ] End-to-end tests for workflow

## Future Phases

### Phase 2: Enhanced Detection (In Progress)

**Goal**: Improve detection accuracy and add advanced analysis

**Recent Additions:**
- [x] Verification status signal (Bluesky verified, HN karma-based trust)
- [x] Multi-query batch collection
- [x] Enhanced frontend with "All Accounts" view
- [x] Comment-based bot detection with 5 new signals
- [x] Detoxify ML-based inflammatory content detection
- [x] Comment harvesting from top-performing posts
- [x] InflammatoryFlagDB and CommentStatsDB tables
- [x] Vue→React migration (React 19, React Router 7)
- [x] Bun native frontend tooling (removed Vite dependency)
- [x] Comment stats UI (3 new cards: Total Comments, Inflammatory, Avg Severity)
- [x] Backend dependency upgrades (FastAPI 0.128, SQLAlchemy 2.0.46, etc.)

**Next Steps:**
- [x] Review Scoring System
  - [x] Signals in the UI not matching bot score (fixed: Pydantic model capped at 10.0, now 22.0)
- [x] Comment/reply analysis
  - [x] Reply pattern detection (comment timing signal)
  - [x] Comment harvesting infrastructure
  - [x] Inflammatory content detection (Detoxify)
  - [x] 5 comment-based scoring signals
- [ ] Automated Testing Suite
  - [ ] Backend unit tests (pytest)
    - [ ] Platform adapter tests (Bluesky, HN)
    - [ ] Detection signal tests (all 13 signals)
    - [ ] Inflammatory detector tests
    - [ ] API endpoint tests
  - [ ] Frontend unit tests (Bun test)
    - [ ] Hook tests (useStats, useAccounts)
    - [ ] Component tests (StatsCards, AccountsTable)
  - [ ] Integration tests
    - [ ] Full collection cycle
    - [ ] End-to-end API flows
  - [ ] CI/CD pipeline (GitHub Actions)
- [ ] Advanced detection algorithms
  - [ ] Sentiment analysis using transformers
  - [ ] Text similarity using sentence embeddings
  - [ ] Benford's Law for engagement numbers
  - [ ] Graph-based bot detection
- [ ] Narrative clustering
  - [ ] Topic modeling
  - [ ] Cross-account narrative correlation
  - [ ] Temporal narrative tracking
- [ ] Content similarity detection
  - [ ] Image similarity (if applicable)
  - [ ] Text deduplication at scale
- [ ] Cross-account coordination detection
  - [ ] Posting time correlation
  - [ ] Content similarity across accounts
  - [ ] Network analysis

### Phase 3: Multi-Platform Expansion

**Goal**: Add more social media platforms

- [ ] Mastodon integration
  - [ ] Instance discovery
  - [ ] Federated timeline access
  - [ ] Account authentication
- [ ] Twitter/X integration (if access available)
  - [ ] API access (expensive tiers)
  - [ ] Rate limiting handling
- [ ] Reddit integration (if access available)
  - [ ] OAuth authentication
  - [ ] Subreddit monitoring
- [ ] Cross-platform correlation
  - [ ] Same accounts across platforms
  - [ ] Coordinated narratives
  - [ ] Cross-platform bot networks

### Phase 4: Visualization & UX

**Goal**: Improve user experience and data visualization

- [ ] Collection Panel enhancements
  - [ ] Multiple query support (batch collection from UI)
  - [ ] Query history/saved queries
- [ ] Comment stats navigation
  - [ ] Dedicated comments/inflammatory page
  - [ ] View individual flagged comments
  - [ ] Comment-to-account drill-down
- [ ] Network graph visualization
  - [ ] D3.js or vis.js integration
  - [ ] Account interaction graphs
  - [ ] Bot network visualization
- [ ] Timeline views
  - [ ] Account activity over time
  - [ ] Narrative evolution
- [ ] Advanced filtering and search
  - [ ] Full-text search
  - [ ] Complex query builder
  - [ ] Saved filters
- [ ] Export functionality
  - [ ] CSV export
  - [ ] JSON export
  - [ ] PDF reports
- [ ] Account comparison views
  - [ ] Side-by-side comparison
  - [ ] Diff visualization
- [ ] Narrative flow diagrams
  - [ ] Topic evolution
  - [ ] Spread visualization

### Phase 5: Production Ready

**Goal**: Deploy to production with enterprise features

- [ ] PostgreSQL migration
  - [ ] Migration scripts
  - [ ] Connection pooling
  - [ ] Query optimization
- [ ] Docker containerization
  - [ ] Multi-stage builds
  - [ ] Docker Compose
  - [ ] Health checks
- [ ] Cloud deployment
  - [ ] Railway configuration
  - [ ] Render configuration
  - [ ] DigitalOcean setup guide
- [ ] Authentication system
  - [ ] User accounts (optional)
  - [ ] API keys
  - [ ] Role-based access
- [ ] API rate limiting
  - [ ] Per-user limits
  - [ ] Redis-based limiting
- [ ] Caching layer
  - [ ] Redis caching
  - [ ] Cache invalidation
- [ ] Automated testing suite
  - [ ] Unit tests (80%+ coverage)
  - [ ] Integration tests
  - [ ] E2E tests
- [ ] CI/CD pipeline
  - [ ] GitHub Actions
  - [ ] Automated deployment
  - [ ] Version tagging

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

**Decision**: Bun + Vue 3 + TypeScript for frontend (initial)
**Rationale**: Modern stack, fast tooling, type safety
**Impact**: Better DX, faster builds, fewer runtime errors

### 2026-01-24 - Vue→React Migration

**Decision**: Migrate from Vue 3 to React 19 with Bun native tooling
**Rationale**: Bun 1.3+ provides native frontend dev server with HMR; eliminates Vite dependency; React Fast Refresh works out of box; simpler build pipeline (`bun index.html` for dev, `bun build` for prod)
**Impact**: Removed Vite, vue-router, Pinia; replaced with React, React Router 7, custom hooks; frontend port changed from 5173 to 3000

**Decision**: Use custom React hooks instead of Pinia stores
**Rationale**: React's built-in useState/useEffect with custom hooks provides equivalent functionality; simpler architecture without additional state management library
**Impact**: useStats, useAccounts, usePlatforms hooks replace Pinia stores

**Decision**: 8 detection signals with 0-13.5 scoring
**Rationale**: Balance between simplicity and accuracy; transparent scoring; verification status adds important trust dimension
**Impact**: Easy to understand, tune thresholds, explain to users; verified accounts less likely to be flagged

**Decision**: Manual trigger for MVP, optional background scheduler
**Rationale**: Better for testing and development; can enable later
**Impact**: More control during development, easier debugging

### 2026-01-25 - Collection Panel UI

**Decision**: Add CollectionPanel component for UI-based data collection
**Rationale**: Users should be able to collect and analyze data without CLI; provides visual feedback on collection progress; simplifies workflow for non-technical users
**Impact**: Full collection workflow accessible from dashboard; platform/query/limit configurable in UI; comment harvesting toggle; combined "Collect & Analyze" action

**Decision**: Enhanced collection API with query parameters
**Rationale**: Original `/api/collection/trigger` only ran full cycle; need granular control for specific queries and limits
**Impact**: API now accepts `query`, `limit`, `harvest_comments` parameters; returns detailed results (posts/accounts/comments collected)

**Decision**: Investigate and document comment collection workflow
**Rationale**: Comment-based detection was implemented but workflow unclear; needed to verify it works during normal collection
**Impact**: Confirmed comment harvesting IS automatic during collection if enabled; identified that scheduler is disabled by default; analysis still requires separate trigger

### 2026-01-24 - shadcn/ui + Dark Mode

**Decision**: Migrate to shadcn/ui component library
**Rationale**: Previous custom CSS had SVG sizing issues; shadcn/ui provides accessible, tested components; built on Radix UI primitives; components are copied into project (no version lock-in)
**Impact**: Modern, polished UI with consistent styling; dark mode support; better accessibility

**Decision**: Add dark mode with system preference detection
**Rationale**: Modern UX expectation; reduces eye strain; respects user preferences
**Impact**: ThemeContext provides toggle and localStorage persistence; system preference detected on first load

**Decision**: Build Tailwind CSS separately before Bun dev server
**Rationale**: Bun's native dev server doesn't process PostCSS; Tailwind requires PostCSS for @apply directives and CSS variables
**Impact**: start.sh now runs `bunx tailwindcss` in watch mode alongside `bun index.html`

### 2026-01-24 - Comment-Based Bot Detection

**Decision**: Add 5 comment-based detection signals (total 13 signals, max 22.0 points)
**Rationale**: Research shows bots operate as "amplification parasites" targeting comment sections of viral content; ~20% of social media chatter on major events comes from bots
**Impact**: Better detection of comment-spamming bots that don't create original content

**Decision**: Use Detoxify ML library for inflammatory detection
**Rationale**: Local ML model (98%+ AUC) without external API dependencies; supports batch inference; lightweight (~500MB RAM)
**Impact**: Fast, accurate toxicity detection without API costs or rate limits

**Decision**: Lazy load Detoxify model on first use
**Rationale**: Model loading takes 5-10 seconds; shouldn't block application startup
**Impact**: Faster startup, model only loaded when inflammatory detection is actually needed

**Decision**: Store comments as Posts with parent_id
**Rationale**: Reuses existing infrastructure; allows unified post/comment analysis
**Impact**: Simpler architecture, consistent data model, efficient queries

### 2026-01-24 - Enhanced Detection

**Decision**: Add verification status as 8th detection signal (0-1.5 points)
**Rationale**: Verified accounts and high-trust users are significantly less likely to be bots; adds important trust dimension
**Impact**: Better accuracy, fewer false positives on verified accounts, max score now 13.5

**Decision**: Weight unverified accounts higher than other profile signals
**Rationale**: Verification is a strong trust signal; unverified + new account is particularly suspicious
**Impact**: Unverified new accounts can score up to 1.5 points vs 1.0 for incomplete profile

**Decision**: Use karma as trust proxy for Hacker News
**Rationale**: HN doesn't have formal verification; karma is community-validated trust metric
**Impact**: High-karma users (≥1000) treated as verified equivalents

## Known Issues

### Recently Fixed ✅
- ✅ Timestamp precision handling (atproto 0.0.65 nanosecond support)
- ✅ Snake_case to camelCase type mismatches in frontend
- ✅ AccountsTable rendering issues with signal badges
- ✅ Button styling (Tailwind custom colors)
- ✅ Stats data transformation
- ✅ Signals not matching bot score (Pydantic model max was 10.0, actual max is 13.5)
- ✅ Bluesky pagination for collecting >100 posts (API limit)

### Minor Issues
- Bluesky account creation date not directly exposed in API (workaround: using current time)
- HN Firebase API doesn't support keyword search (would need Algolia integration)
- Some npm audit warnings (moderate severity, breaking changes to fix)

### Performance Considerations
- SQLite may struggle with >100k accounts (migration to PostgreSQL recommended)
- Content similarity detection is O(n²) for large datasets (needs optimization)
- ✅ Pagination added to frontend tables with configurable page sizes (50-1000) and offset-based API

### Security Considerations
- No authentication on API (intentional for MVP, but needed for production)
- Bluesky credentials in plaintext .env file (acceptable for local dev only)
- CORS allows all origins in dev mode (needs restriction for production)

## Performance Metrics

_Tracked once data collection begins_

- Posts collected (Bluesky): **TBD**
- Posts collected (HN): **TBD**
- Accounts analyzed: **TBD**
- Flags generated: **TBD**
- False positive rate: **TBD** (requires manual verification)
- Collection cycle time: **TBD**
- Analysis cycle time: **TBD**
- Database size: **TBD**

## Notes for Future Development

### Platform-Specific Considerations

**Bluesky:**
- Account creation date not directly exposed - consider implementing DID resolution for better tracking
- AT Protocol supports custom feeds - potential future feature for curated bot detection feeds
- Labeling system could be integrated for community-driven bot reporting
- PDS (Personal Data Server) architecture allows for decentralized deployment

**Hacker News:**
- No followers/following concept - adjust detection signals accordingly
- Karma system is unique - different engagement metric than likes/reposts
- Consider Algolia HN Search API integration for better search (https://hn.algolia.com/api)
- Comments are valuable signal - analyze comment patterns in Phase 2
- Story vs comment submissions should be weighted differently

### Detection Algorithm Ideas

**High Priority:**
- Implement text similarity using sentence transformers (SentenceTransformers library)
- Add temporal pattern analysis with hourly posting heatmaps
- Consider Benford's Law analysis for suspicious engagement numbers
- Implement graph-based detection for follower/following networks

**Medium Priority:**
- Language detection and multilingual support
- Emoji usage patterns (bots often overuse or underuse)
- Link sharing patterns (spam bots share many links)
- Response time analysis (bots often respond instantly)

**Low Priority:**
- Profile picture similarity (requires computer vision)
- Bio text similarity across accounts
- Geolocation patterns (if available)

### Architecture Improvements

**Database:**
- Add Redis for caching frequently accessed data
- Implement database connection pooling for PostgreSQL
- Consider time-series database for temporal analysis (InfluxDB, TimescaleDB)
- Add full-text search index for content search

**API:**
- Add GraphQL endpoint for flexible queries
- Implement webhook system for real-time alerts
- Add batch operations for bulk analysis
- Consider gRPC for internal services

**Frontend:**
- Add real-time updates using WebSockets
- Implement infinite scroll for large datasets
- ✅ Add dark mode support (completed with shadcn/ui)
- Consider mobile app (React Native or Flutter)

### Deployment Considerations

**Railway:**
- Easiest deployment option
- Automatic HTTPS
- PostgreSQL addon available
- ~$5/month for hobby plan

**Render:**
- Free tier available
- Good for MVP
- PostgreSQL included
- Auto-deploy from GitHub

**DigitalOcean:**
- More control
- App Platform or Droplets
- ~$5-12/month
- Managed PostgreSQL available

### Data Privacy & Ethics

**Important Considerations:**
- All data collected is public
- Bot detection is probabilistic, not definitive
- False positives are possible and should be expected
- Users should verify findings before taking action
- Consider implementing appeal/review system
- Respect platform ToS and rate limits
- Don't use for harassment or coordinated reporting

## Success Metrics for MVP

- [x] Successfully collect data from Bluesky
- [x] Successfully collect data from Hacker News
- [x] Store at least 100 posts in database
- [x] Identify at least 1 suspicious account
- [x] CLI tool works end-to-end
- [x] Web dashboard displays data correctly
- [ ] Run for 24 hours without crashes (pending testing)
- [ ] Flag rate between 1-10% (pending real data)

## Resources & References

**Documentation:**
- Bluesky AT Protocol: https://atproto.com/
- Hacker News API: https://github.com/HackerNews/API
- FastAPI: https://fastapi.tiangolo.com/
- React 19: https://react.dev/
- React Router 7: https://reactrouter.com/
- Bun: https://bun.sh/

**Research:**
- Bot detection literature (add references as researched)
- Social network analysis papers
- NLP for bot detection

## Contributors

- Initial development: Purisa Team
- See GitHub for contributor list

---

Last Updated: 2026-01-25
Version: 0.6.0 (Collection Panel UI)
