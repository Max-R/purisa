# Purisa - Multi-Platform Social Media Bot Detection System

Purisa is an open-source bot detection tool for social media platforms, designed to identify suspicious accounts and coordinated bot activity. Currently supports **Bluesky** (primary) and **Hacker News** (secondary), with plans to expand to Mastodon, Twitter/X, and Reddit.

## Features

- **Multi-Platform Support**: Platform-agnostic architecture using adapter pattern
- **13 Detection Signals**: Comprehensive bot detection using multiple behavioral indicators (8 core + 5 comment-based)
- **Comment-Based Detection**: ML-powered inflammatory content detection targeting "amplification parasites"
- **Real-Time Collection**: Automated data collection from social media platforms
- **Web Dashboard**: React 19 + TypeScript dashboard with Bun native tooling
- **CLI Tool**: Command-line interface for manual operations
- **RESTful API**: FastAPI backend with full API documentation
- **Extensible**: Easy to add new platforms and detection signals

## Detection Signals

Purisa uses a **multi-signal approach** to detect bot-like behavior, analyzing 13 different behavioral indicators. Each signal contributes to a total score from 0-22.0, with accounts scoring **≥7.0 flagged as suspicious**.

### Core Signals (8 signals, max 12.5 points)

These signals analyze general account behavior and posting patterns.

### How Scoring Works

Each account is analyzed independently, and signals are scored based on specific thresholds. The scores are **additive** - all signal scores are summed to create the total bot score.

#### 1. **New Account** (0-2 points)

Checks if the account was created recently, as new accounts are commonly associated with bot campaigns.

**Scoring Logic:**
- **2.0 points**: Account less than 7 days old (very suspicious)
- **1.0 points**: Account between 7-30 days old (moderately suspicious)
- **0.0 points**: Account older than 30 days

**Why this matters:** Bot campaigns often involve mass account creation. Legitimate users typically have older, established accounts.

**Configuration:** Adjust `NEW_ACCOUNT_DAYS` in `backend/.env` (default: 30)

---

#### 2. **High Frequency Posting** (0-3 points)

Analyzes posting rate over the last 24 hours to detect impossibly high activity that suggests automation.

**Scoring Logic:**
- **3.0 points**: >10 posts/hour (240+ posts/day)
- **2.0 points**: >5 posts/hour (120+ posts/day)
- **1.0 points**: >2 posts/hour (48+ posts/day)
- **0.0 points**: ≤2 posts/hour

**Why this matters:** Humans have physical limits on posting frequency. High rates suggest automated posting.

**Note:** Only analyzes posts from the last 24 hours for recency.

---

#### 3. **Repetitive Content** (0-2.5 points)

Detects duplicate or near-duplicate posts using exact matching and Jaccard similarity on word sets.

**Scoring Logic:**
- **2.5 points**: >30% exact duplicates OR >70% content similarity
- **1.5 points**: >10% exact duplicates OR >50% content similarity
- **0.5 points**: >5% exact duplicates OR >30% content similarity
- **0.0 points**: <5% duplicates and <30% similarity

**Analysis Method:**
1. Takes last 100 posts
2. Checks for exact duplicate content (case-insensitive)
3. Calculates Jaccard similarity between word sets
4. Each post compared to next 10 posts (prevents O(n²) explosion)

**Why this matters:** Bots often repost the same message repeatedly. Humans naturally vary their content.

---

#### 4. **Low Engagement** (0-1.5 points)

Flags accounts with high post volume but suspiciously low interaction (likes, reposts, replies).

**Scoring Logic:**
- **1.5 points**: >100 posts with <1 avg engagement per post
- **1.0 points**: >50 posts with <2 avg engagement per post
- **0.5 points**: >20 posts with <3 avg engagement per post
- **0.0 points**: Otherwise

**Engagement Calculation:**
- **Bluesky**: Sums likes + reposts + replies
- **Hacker News**: Sums score + comments

**Why this matters:** Legitimate accounts typically build engagement over time. Bots often post into the void with little interaction.

**Minimum posts:** Requires ≥10 posts to avoid false positives on new legitimate accounts.

---

#### 5. **Generic Username** (0-1 point)

Detects bot-like username patterns using regex matching.

**Scoring Logic:**
- **1.0 points**: Matches a bot pattern
- **0.5 points**: Username <3 or >30 characters (outlier length)
- **0.0 points**: Normal username

**Bot Patterns Detected:**
- `wordNNNN` → e.g., "alice1234", "news5678"
- `word_wordNN` → e.g., "crypto_bot99"
- `*bot*` → Any username containing "bot"
- `userNNN` → e.g., "user123", "user4567"
- `abNNNNNN` → Very short letters + many numbers (e.g., "xy123456")

**Why this matters:** Automated account generation often produces predictable username patterns.

---

#### 6. **Incomplete Profile** (0-1 point)

Checks for missing profile information, as bots often skip profile setup.

**Scoring Logic (Platform-Specific):**

**Bluesky:**
- **1.0 points**: Missing both description AND avatar
- **0.5 points**: Missing description OR avatar
- **0.0 points**: Has both description and avatar

**Hacker News:**
- **1.0 points**: No "about" section AND <10 karma
- **0.5 points**: No "about" section OR <5 karma
- **0.0 points**: Has "about" or sufficient karma

**Why this matters:** Legitimate users invest time in their profiles. Bots prioritize volume over presentation.

---

#### 7. **Temporal Pattern** (0-1 point)

Detects unnatural posting patterns, particularly 24/7 activity that suggests automation.

**Scoring Logic:**
- **1.0 points**: Posts in >20 different hours (nearly 24/7 posting)
- **0.5 points**: Posts in >16 different hours
- **0.0 points**: Posts in ≤16 different hours

**Analysis Method:**
1. Extracts hour of day for each post (0-23)
2. Counts number of unique hours with activity
3. Flags accounts posting around the clock

**Why this matters:** Humans have sleep cycles and daily routines. Bots operate continuously.

**Minimum posts:** Requires ≥20 posts to ensure statistical significance.

---

#### 8. **Unverified Account** (0-1.5 points)

Checks verification status and trust signals to identify accounts lacking credibility markers.

**Scoring Logic (Platform-Specific):**

**Bluesky:**
- **0.0 points**: Verified account (blue checkmark)
- **1.5 points**: Unverified + <7 days old (very suspicious)
- **1.0 points**: Unverified + 7-30 days old (suspicious)
- **0.5 points**: Unverified + >30 days old (mildly suspicious)

**Hacker News:**
- **0.0 points**: ≥1000 karma (established, trusted user)
- **0.3 points**: ≥100 karma (active user)
- **0.7 points**: ≥10 karma (minimal activity)
- **1.5 points**: <10 karma (new/inactive account)

**Why this matters:** Verified accounts and high-karma users have established trust. Unverified accounts, especially when new, are more likely to be bots.

**Note:** Bluesky verification indicates domain ownership or official status. HN uses karma as a proxy for community trust.

---

### Comment-Based Signals (5 signals, max 9.5 points)

These signals specifically target "amplification parasites" - bots that operate in comment sections of high-performing posts with inflammatory content rather than creating original content.

**How Comment Detection Works:**

1. **Identify Top Performers**: During collection, posts with high engagement scores (≥0.01 normalized) are flagged
2. **Harvest Comments**: Comments are collected from top-performing posts
3. **Fetch Commenter Profiles**: Full profiles are fetched for new commenter accounts (batched, with progress logging)
4. **Detect Inflammatory Content**: ML-based toxicity detection (Detoxify) analyzes comment text
5. **Flag Accounts**: Accounts posting inflammatory comments are queued for full bot analysis

**Note:** Full profile fetching for commenters enables all 13 detection signals. Without profiles, only the 5 comment-based signals would apply. This can be disabled via `fetch_commenter_profiles: false` in `platforms.yaml` for faster collection.

---

#### 9. **Comment Repetitiveness** (0-2 points)

Detects duplicate or near-duplicate comments across multiple posts.

**Scoring Logic:**
- **2.0 points**: >50% of comments are duplicates/near-duplicates
- **1.5 points**: >30% repetitive comments
- **1.0 points**: >15% repetitive comments
- **0.0 points**: <15% repetitive comments

**Analysis Method:**
- Exact duplicate detection (case-insensitive)
- Jaccard similarity for near-duplicates (>70% word overlap)

**Why this matters:** Bots often spam the same comment across multiple posts. Legitimate users vary their contributions.

---

#### 10. **Comment Timing** (0-2.5 points)

Analyzes commenting speed to detect impossibly fast responses.

**Scoring Logic:**
- **2.5 points**: >50% of comments posted within 30 seconds of each other
- **2.0 points**: >30% rapid-fire comments
- **1.0 points**: >15% rapid-fire comments
- **0.0 points**: <15% rapid-fire comments

**Why this matters:** Humans need time to read posts and compose thoughtful responses. Bots can post instantly.

---

#### 11. **Inflammatory Frequency** (0-2 points)

Measures the proportion of comments flagged as toxic/inflammatory.

**Scoring Logic:**
- **2.0 points**: >50% of comments are inflammatory
- **1.5 points**: >30% inflammatory comments
- **1.0 points**: >15% inflammatory comments
- **0.0 points**: <15% inflammatory comments

**Detection Categories (via Detoxify ML):**
- `toxic`: General toxicity
- `severe_toxic`: Highly toxic content
- `obscene`: Profanity/obscenity
- `threat`: Threatening language
- `insult`: Insulting language
- `identity_hate`: Identity-based attacks

**Why this matters:** Bots are often deployed to spread divisive content and inflame discussions.

---

#### 12. **Comment-to-Post Ratio** (0-1.5 points)

Identifies accounts that only comment and never create original content.

**Scoring Logic:**
- **1.5 points**: Account has 0 original posts (only comments)
- **1.5 points**: >20:1 comment-to-post ratio
- **1.0 points**: >10:1 ratio
- **0.5 points**: >5:1 ratio
- **0.0 points**: ≤5:1 ratio

**Why this matters:** Legitimate users typically create some original content. Bots often exist solely to amplify others' posts.

---

#### 13. **Comment Engagement Ratio** (0-1.5 points)

Detects comments that receive suspiciously low engagement.

**Scoring Logic:**
- **1.5 points**: <0.1 average engagement per comment AND <10% of comments have any engagement
- **1.0 points**: <0.5 avg engagement AND <20% with engagement
- **0.0 points**: Otherwise

**Why this matters:** Low-quality bot comments typically receive no likes or replies, while legitimate engagement generates responses.

---

### Total Score Calculation

**Formula:** `Total Score = sum(all signal scores)`

**Maximum Possible Score:** 22.0 points

**Core Signals (12.5 points max):**
- New Account: 2.0
- High Frequency: 3.0
- Repetitive Content: 2.5
- Low Engagement: 1.5
- Generic Username: 1.0
- Incomplete Profile: 1.0
- Temporal Pattern: 1.0
- Unverified Account: 1.5

**Comment-Based Signals (9.5 points max):**
- Comment Repetitiveness: 2.0
- Comment Timing: 2.5
- Inflammatory Frequency: 2.0
- Comment-to-Post Ratio: 1.5
- Comment Engagement Ratio: 1.5

**Flagging Threshold:** ≥7.0 (configurable via `BOT_DETECTION_THRESHOLD` in `.env`)

**Example Scores:**
- **Score 11.0** (Highly Suspicious): New account (2.0) + High frequency (3.0) + Repetitive content (2.5) + Low engagement (1.0) + Incomplete profile (1.0) + Unverified (1.5)
- **Score 7.5** (Flagged): High frequency (3.0) + Repetitive content (2.5) + Generic username (1.0) + Unverified (1.0)
- **Score 3.5** (Clean): New account (1.0) + Some repetitive content (1.5) + Incomplete profile (1.0)
- **Score 0.0** (Very Clean): Verified account with normal posting patterns

---

### Platform-Specific Differences

**Bluesky:**
- Profile checks: description, avatar
- Engagement: likes, reposts, replies
- Username format: handle.bsky.social

**Hacker News:**
- Profile checks: about section, karma score
- Engagement: story score, comment count
- Username format: plain username
- Verification: karma-based trust (≥1000 = highly trusted)

**Note:** Core behavioral signals (frequency, repetition, temporal) are platform-agnostic.

## Architecture

### Backend (Python)
- **FastAPI**: RESTful API with automatic documentation
- **SQLAlchemy**: ORM with SQLite (PostgreSQL-ready)
- **atproto**: Official Bluesky AT Protocol library
- **httpx**: Async HTTP client for Hacker News API
- **APScheduler**: Background jobs for data collection
- **Pydantic**: Data validation and settings management

### Frontend (TypeScript)
- **Bun**: Fast JavaScript runtime with native frontend tooling (no Vite needed)
- **React 19**: Modern React with hooks
- **shadcn/ui**: Accessible component library built on Radix UI primitives
- **TailwindCSS**: Utility-first styling with CSS variables for theming
- **Axios**: HTTP client for API calls
- **Dark Mode**: System-aware theme toggle with localStorage persistence

## Project Structure

```
purisa/
├── backend/
│   ├── purisa/
│   │   ├── platforms/       # Platform adapters
│   │   │   ├── base.py     # Abstract interface
│   │   │   ├── bluesky.py  # Bluesky implementation
│   │   │   └── hackernews.py
│   │   ├── models/          # Pydantic models
│   │   ├── database/        # SQLAlchemy models
│   │   ├── services/        # Collector & analyzer
│   │   ├── api/             # FastAPI routes
│   │   └── config/          # Settings & config
│   ├── .env.example         # Environment template (copy to .env)
│   ├── requirements.txt
│   └── setup.py
├── frontend/
│   ├── src/
│   │   ├── api/            # API client
│   │   ├── types/          # TypeScript types
│   │   ├── hooks/          # React hooks (state management)
│   │   ├── components/     # React components
│   │   │   └── ui/         # shadcn/ui components
│   │   ├── contexts/       # React contexts (ThemeContext)
│   │   ├── lib/            # Utilities (cn helper)
│   │   ├── App.tsx         # Main app with dashboard
│   │   └── index.tsx       # React entry point
│   └── package.json
├── cli.py                  # CLI tool
├── AGENTS.md              # Development progress
└── README.md
```

## Quick Start

**First time setup:**

```bash
# 1. Clone the repository
git clone <repository-url>
cd purisa

# 2. Set up backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..

# 3. Set up frontend
cd frontend
bun install
cd ..

# 4. Configure credentials
cp backend/.env.example backend/.env
# Edit backend/.env and add your Bluesky handle and app password

# 5. Start everything
./start.sh

# 6. Open dashboard at http://localhost:3000
```

**If you already have dependencies installed:**

```bash
./start.sh

# To stop all servers:
./stop.sh
```

The startup script will automatically initialize the database, build Tailwind CSS, and start both backend and frontend servers.

### CLI Quick Start

**Install the `purisa` command (optional but recommended):**

```bash
chmod +x install.sh
./install.sh
```

**Now use the clean CLI interface:**

```bash
# Instead of: python3 cli.py collect --platform bluesky --query "#politics" --limit 50
# Just type:
purisa collect --platform bluesky --query "#politics" --limit 50

# Other commands
purisa analyze
purisa flagged
purisa stats

# See all commands
purisa --help
```

**Full CLI documentation:** See [CLI_MANUAL.md](CLI_MANUAL.md) for complete command reference and examples.

---

## Detailed Setup Instructions

### Prerequisites

- **Python 3.9+**
- **Bun** (or Node.js 18+)
- **Bluesky Account** (for data collection)

### 1. Clone Repository

```bash
git clone <repository-url>
cd purisa
```

### 2. Backend Setup

```bash
# Create virtual environment
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Deactivate for now
deactivate
cd ..
```

### 3. Frontend Setup

```bash
cd frontend
bun install  # or: npm install
cd ..
```

### 4. Get Bluesky Credentials

1. **Log into Bluesky**: https://bsky.app
2. **Go to Settings** → **App Passwords**: https://bsky.app/settings/app-passwords
3. **Create New App Password**:
   - Click "Add App Password"
   - Name it: "Purisa Bot Detection"
   - Click "Create"
4. **Copy the Password**:
   - ⚠️ **IMPORTANT**: Copy it immediately! You won't see it again!
   - Format: `xxxx-xxxx-xxxx-xxxx`

### 5. Configure Environment Variables

Copy the example environment file and add your credentials:

```bash
cd backend
cp .env.example .env
```

Then edit `backend/.env` and add your Bluesky credentials:

```env
# Bluesky Credentials (REQUIRED)
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_PASSWORD=your-app-password-here

# Database (default is fine)
DATABASE_URL=sqlite:///./purisa.db

# API Settings (default is fine)
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS_STR=http://localhost:3000,http://localhost:5173

# Detection Settings (optional customization)
BOT_DETECTION_THRESHOLD=7.0
NEW_ACCOUNT_DAYS=30
```

**Example:**
```env
BLUESKY_HANDLE=alice.bsky.social
BLUESKY_PASSWORD=abcd-1234-efgh-5678
```

> **Note:** The `.env` file is gitignored for security. Never commit your credentials!

### 6. Start Purisa (Easy Method)

```bash
# From project root - this starts everything!
./start.sh
```

The startup script will:
- ✓ Initialize database (if needed)
- ✓ Start backend API server on http://localhost:8000
- ✓ Start frontend dashboard on http://localhost:3000
- ✓ Show you where everything is running

**To stop all servers:**
```bash
./stop.sh
```

---

## Running Purisa

### Method 1: Automated Startup (Recommended)

```bash
./start.sh
```

**What you'll see:**
- 📊 Database initialization (first time only)
- 🔧 Backend API running on http://localhost:8000
- 🎨 Frontend dashboard on http://localhost:3000

**Access Points:**
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

**Stop servers:**
```bash
./stop.sh
# Or press Ctrl+C in the terminal running start.sh
```

### Method 2: Manual Startup (For Development)

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate
python3 -m uvicorn purisa.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
bun index.html  # Bun's native dev server with HMR
```

**Terminal 3 - CLI Commands:**
```bash
# Initialize database (first time only)
python3 cli.py init

# Collect data
python3 cli.py collect --platform bluesky --query "#politics" --limit 50

# Analyze accounts
python3 cli.py analyze

# View flagged accounts
python3 cli.py flagged
```

---

## Using Purisa

### Using the CLI

With Purisa running (`./start.sh`), open a new terminal for CLI operations:

```bash
# Collect data from Bluesky
purisa collect --platform bluesky --query "#politics" --limit 50

# Analyze all accounts for bots
purisa analyze

# View flagged accounts
purisa flagged

# Show statistics
purisa stats
```

**For complete CLI documentation with examples and workflows, see [CLI_MANUAL.md](CLI_MANUAL.md)**

### Using the Web Dashboard

Open http://localhost:3000 in your browser to see:
- **Collection Panel**: Run data collection directly from the UI
  - Select platform (Bluesky or Hacker News)
  - Multi-query support: add multiple queries as chips, collect from all in one click
  - Configure post limit (50-5000)
  - Toggle comment harvesting from top-performing posts
  - Run "Collect Only", "Analyze Only", or "Collect & Analyze" in one click
- **Stats Cards**: 7 cards showing accounts, posts, flagged accounts, flag rate, plus comment statistics (total comments, inflammatory flags, average severity)
- **Accounts Table**: Bot scores, signals, and account details with tabs for All/Flagged
  - **Comment stats column**: Shows comment count with inflammatory indicators per account
- **Platform Filter**: View data from specific platforms
- **Refresh Button**: Update data in real-time
- **Dark Mode Toggle**: Switch between light and dark themes (respects system preference)

### Enabling Automatic Background Collection

To enable automatic background collection and analysis:

1. Edit `backend/purisa/main.py`
2. Uncomment lines 34-37 in the `lifespan` function:

```python
global scheduler
scheduler = BackgroundScheduler()
scheduler.start()
logger.info("Background scheduler started")
```

3. Restart the backend

This will:
- Collect data every 10 minutes (configurable)
- Analyze accounts every 30 minutes
- Run continuously in the background

## CLI Commands

The Purisa CLI provides commands for data collection, analysis, and viewing results with real-time progress tracking.

**Quick Reference:**
```bash
purisa init                                      # Initialize database
purisa collect --platform bluesky --query "#AI" --limit 50
purisa collect --platform bluesky --query "#politics" --no-harvest-comments
purisa analyze                                   # Analyze all accounts (with progress bar)
purisa flagged                                   # View flagged accounts
purisa stats                                     # Show statistics
```

**Features:**
- Progress bars for collection and analysis operations (requires `tqdm`)
- Comment harvesting with top performer stats (shows qualifying posts, thresholds, capping)
- Multi-query support (collect from multiple queries in one command)

**📖 Full CLI Documentation:** See [CLI_MANUAL.md](CLI_MANUAL.md) for:
- Complete command reference
- Multi-query collection examples
- Workflow guides
- Best practices and tips
- Troubleshooting

## API Endpoints

### Health & Status
- `GET /api/health` - Health check
- `GET /api/platforms/status` - Available platforms

### Accounts
- `GET /api/accounts/all?platform={platform}&limit=50&include_comment_stats=true` - Get all accounts with optional comment stats
- `GET /api/accounts/flagged?platform={platform}&limit=50&include_comment_stats=true` - Get flagged accounts with optional comment stats
- `GET /api/accounts/{platform}/{account_id}` - Account details

### Posts
- `GET /api/posts?platform={platform}&flagged=true&limit=50` - Get posts

### Statistics
- `GET /api/stats/overview?platform={platform}` - Overview statistics
- `GET /api/stats/comments` - Comment collection statistics

### Comments & Inflammatory Detection
- `GET /api/comments/inflammatory` - List inflammatory comments with filters
- `GET /api/posts/{platform}/{post_id}/comments` - Get comments for a post
- `GET /api/accounts/{platform}/{account_id}/comment-stats` - Account comment behavior stats

### Manual Triggers
- `POST /api/collection/trigger?platform={platform}` - Trigger collection
- `POST /api/analysis/trigger?account_id={id}` - Trigger analysis

Full API documentation available at http://localhost:8000/docs

## Configuration

### Platform Targets

Edit `backend/purisa/config/platforms.yaml`:

```yaml
bluesky:
  enabled: true
  targets:
    hashtags:
      - politics
      - election2024
    keywords:
      - "supreme court"
  collection:
    refresh_interval: 600  # 10 minutes
    posts_per_cycle: 100

hackernews:
  enabled: true
  targets:
    types:
      - top
      - new
  collection:
    refresh_interval: 1800  # 30 minutes
    posts_per_cycle: 50

# Comment harvesting settings
comment_collection:
  enabled: true
  min_engagement_score: 0.01  # Minimum normalized score for "top performer"
  max_comments_per_post: 100
  max_posts_for_comment_harvest: 50
  fetch_commenter_profiles: true  # Fetch full profiles for commenters (enables all 13 signals)
```

### Detection Thresholds

Edit `backend/.env`:

```env
BOT_DETECTION_THRESHOLD=7.0    # Flag threshold (0-22)
NEW_ACCOUNT_DAYS=30            # Days to consider "new"
HIGH_FREQUENCY_THRESHOLD=50    # Posts per hour

# Inflammatory Detection (Detoxify ML)
INFLAMMATORY_MODEL=original-small    # 'original-small', 'original', or 'unbiased'
INFLAMMATORY_THRESHOLD=0.5           # Score threshold (0.0-1.0)
INFLAMMATORY_DEVICE=cpu              # 'cpu' or 'cuda' for GPU

# Comment Collection
COMMENT_COLLECTION_ENABLED=true
COMMENT_MIN_ENGAGEMENT_SCORE=0.3
COMMENT_MAX_PER_POST=100
COMMENT_MAX_POSTS_PER_CYCLE=50
```

## Development

### Adding a New Platform

1. Create adapter in `backend/purisa/platforms/new_platform.py`:

```python
from .base import SocialPlatform

class NewPlatform(SocialPlatform):
    async def collect_posts(self, query: str, limit: int) -> List[Post]:
        # Implementation
        pass

    async def get_account_info(self, username: str) -> Account:
        # Implementation
        pass

    # ... implement other abstract methods
```

2. Register in `backend/purisa/services/collector.py`
3. Add configuration to `platforms.yaml`
4. Update frontend types if needed

### Adding a New Detection Signal

Edit `backend/purisa/services/analyzer.py`:

```python
def _check_new_signal(self, account: AccountDB, posts: List[PostDB]) -> float:
    """
    Description of signal.

    Returns:
        Signal score (0-X)
    """
    # Implementation
    return score
```

Add to `analyze_account()` method's signals dict.

## Database

### SQLite (Development)
Default configuration uses SQLite (`purisa.db`)

### PostgreSQL (Production)

Update `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/purisa
```

SQLAlchemy will automatically adapt.

## Deployment

### Docker (Coming Soon)

```bash
docker-compose up
```

### Cloud Platforms

Purisa can be deployed to:
- **Railway**: Easy deployment with automatic HTTPS
- **Render**: Free tier available
- **DigitalOcean**: App Platform or Droplets
- **Fly.io**: Global edge deployment

Configuration guide coming in Phase 5.

## Roadmap

### Phase 1: MVP (Complete)
- ✅ Bluesky & Hacker News support
- ✅ 8 core detection signals (including verification status)
- ✅ Web dashboard with "All Accounts" and "Flagged" views
- ✅ CLI tool with multi-query support
- ✅ SQLite database

### Phase 2: Enhanced Detection (In Progress)
- ✅ Verification/trust signals (Bluesky verification, HN karma)
- ✅ Comment/reply analysis with inflammatory detection
- ✅ Detoxify ML-based toxicity detection (98%+ AUC)
- ✅ 5 new comment-based scoring signals
- 🔄 Sentiment analysis
- 🔄 Narrative clustering
- 🔄 Content similarity detection
- 🔄 Cross-account coordination

### Phase 3: Multi-Platform Expansion
- Mastodon integration
- Twitter/X integration (if access available)
- Reddit integration (if access available)
- Cross-platform correlation

### Phase 4: Visualization & UX
- Network graph visualization (D3.js)
- Timeline views
- Advanced filtering
- Export functionality (CSV, JSON)
- Account comparison

### Phase 5: Production Ready
- PostgreSQL migration
- Docker containerization
- Cloud deployment guides
- Authentication system
- API rate limiting
- Redis caching
- Automated testing
- CI/CD pipeline

## Troubleshooting

### "Platform not available" error
- Check that environment variables are set correctly
- For Bluesky: Verify handle and app password
- Run `python3 cli.py init` to verify configuration

### "Database not initialized" error
- Run `python3 cli.py init`
- Check `DATABASE_URL` in `.env`

### Frontend can't connect to backend
- Verify backend is running on http://localhost:8000
- Check CORS settings in `backend/.env`
- Ensure both ports 3000 (frontend) and 8000 (backend) are available

### No data collecting from Bluesky
- Verify credentials are correct
- Check if account is in good standing
- Try a different hashtag/query
- Check backend logs for errors

## Contributing

Contributions welcome! Please see AGENTS.md for current development status.

Areas we'd love help with:
- Additional platform adapters (Mastodon, Reddit, etc.)
- Advanced detection algorithms
- Visualization improvements
- Documentation
- Testing

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **Bluesky Team**: For the open AT Protocol
- **Hacker News**: For the public API
- **FastAPI & Vue Communities**: For excellent frameworks

## Contact

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: Purisa is a research and analysis tool. Always verify findings manually before taking action based on bot detection results. False positives are possible.
