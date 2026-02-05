# Purisa - Multi-Platform Coordination Detection System

Purisa is an open-source tool for detecting **coordinated inauthentic behavior** on social media platforms. Unlike traditional bot detection that scores individual accounts, Purisa 2.0 uses **network analysis** to identify patterns of coordinated activity across accounts.

Currently supports **Bluesky** (primary) and **Hacker News** (secondary), with plans to expand to Mastodon, Twitter/X, and Reddit.

## What's New in 2.0

Purisa 2.0 represents a paradigm shift from individual account scoring to **network-based coordination detection**:

| Before (v1.x) | After (v2.0) |
|---------------|--------------|
| Score individual accounts | Analyze network patterns |
| "Account X is 7.2/10 suspicious" | "23% coordinated activity this hour" |
| Flag individual users | Detect coordination clusters |
| 13 heuristic signals | Graph similarity + temporal patterns |

## Features

- **Coordination Detection**: Network-based analysis to detect coordinated posting campaigns
- **Multi-Platform Support**: Platform-agnostic architecture using adapter pattern
- **Hourly Scoring**: Continuous coordination score (0-100) for each hour
- **Spike Detection**: Automatic identification of unusual coordination activity
- **Cluster Detection**: Louvain community detection for finding coordinated groups
- **Real-Time Collection**: Automated data collection from social media platforms
- **Web Dashboard**: React 19 + TypeScript dashboard with Bun native tooling
- **CLI Tool**: Command-line interface for collection, analysis, and monitoring
- **RESTful API**: FastAPI backend with full API documentation
- **Historical Tracking**: Store metrics over time for trend analysis

## How Coordination Detection Works

Purisa analyzes social media activity using network analysis to detect coordinated behavior:

### 1. Build Similarity Networks

For each hour, Purisa builds a network graph where:
- **Nodes** = Accounts that posted during the hour
- **Edges** = Detected coordination signals between accounts

### 2. Coordination Signals

Edges are created when accounts exhibit coordinated behavior:

| Signal | Description | Weight |
|--------|-------------|--------|
| **Synchronized Posting** | Posts within 90 seconds of each other | 1.0 |
| **URL Sharing** | Sharing the same links | 1.5 |
| **Text Similarity** | TF-IDF cosine similarity > 0.8 | 1.0 |
| **Hashtag Overlap** | 2+ shared hashtags | 0.5 |
| **Reply Patterns** | Commenting on the same posts | 0.8 |

### 3. Cluster Detection

Using **Louvain community detection**, Purisa identifies clusters of tightly connected accounts:
- Minimum cluster size: 3 accounts
- Minimum density: 0.3 (30% of possible edges present)

### 4. Coordination Score

Each hour receives a coordination score (0-100) based on:
- **Cluster Coverage** (40%): % of posts from clustered accounts
- **Cluster Density** (30%): How tightly connected clusters are
- **Sync Rate** (30%): Rate of synchronized posting

### 5. Spike Detection

Purisa uses z-score analysis to identify unusual activity:
- Calculates baseline mean and standard deviation
- Flags hours that exceed 2+ standard deviations
- Highlights potential coordinated campaigns

## Architecture

### Backend (Python)
- **FastAPI**: RESTful API with automatic documentation
- **SQLAlchemy**: ORM with SQLite (PostgreSQL-ready)
- **NetworkX**: In-memory graph analysis for coordination detection
- **scikit-learn**: TF-IDF vectorization for text similarity
- **pandas**: Time-series aggregation
- **atproto**: Official Bluesky AT Protocol library
- **httpx**: Async HTTP client for Hacker News API
- **APScheduler**: Background jobs for data collection
- **Pydantic**: Data validation and settings management

### Frontend (TypeScript)
- **Bun**: Fast JavaScript runtime with native frontend tooling
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
│   │   ├── platforms/           # Platform adapters
│   │   │   ├── base.py          # Abstract interface
│   │   │   ├── bluesky.py       # Bluesky implementation
│   │   │   └── hackernews.py    # HackerNews implementation
│   │   ├── models/              # Pydantic models
│   │   ├── database/            # SQLAlchemy models
│   │   │   ├── models.py        # Core tables (accounts, posts)
│   │   │   └── coordination_models.py  # Coordination tables (NEW)
│   │   ├── services/            # Business logic
│   │   │   ├── collector.py     # Data collection
│   │   │   ├── coordination.py  # Coordination analyzer (NEW)
│   │   │   └── similarity.py    # Text similarity (NEW)
│   │   ├── api/                 # FastAPI routes
│   │   └── config/              # Settings & config
│   ├── .env.example             # Environment template
│   ├── requirements.txt
│   └── setup.py
├── frontend/
│   ├── src/
│   │   ├── api/                 # API client
│   │   ├── types/               # TypeScript types
│   │   ├── hooks/               # React hooks
│   │   ├── components/          # React components
│   │   │   └── ui/              # shadcn/ui components
│   │   ├── contexts/            # React contexts
│   │   ├── lib/                 # Utilities
│   │   ├── App.tsx              # Main app
│   │   └── index.tsx            # Entry point
│   └── package.json
├── cli.py                       # CLI tool
├── CHANGELOG.md                    # Development progress
├── CLI_MANUAL.md                # CLI documentation
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

### CLI Quick Start

**Install the `purisa` command (optional but recommended):**

```bash
chmod +x install.sh
./install.sh
```

**Basic workflow:**

```bash
# Initialize database
purisa init

# Collect data from Bluesky
purisa collect --platform bluesky --query "#politics" --limit 100

# Run coordination analysis
purisa analyze --platform bluesky --hours 6

# Check for coordination spikes
purisa spikes --platform bluesky

# View statistics
purisa stats
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
   - Name it: "Purisa Coordination Detection"
   - Click "Create"
4. **Copy the Password**:
   - ⚠️ **IMPORTANT**: Copy it immediately! You won't see it again!
   - Format: `xxxx-xxxx-xxxx-xxxx`

### 5. Configure Environment Variables

```bash
cd backend
cp .env.example .env
```

Edit `backend/.env`:

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
```

### 6. Start Purisa

```bash
# From project root - this starts everything!
./start.sh
```

**Access Points:**
- **Dashboard**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

---

## Using Purisa

### Using the CLI

```bash
# Collect data from Bluesky
purisa collect --platform bluesky --query "#politics" --limit 100

# Collect from multiple topics
purisa collect --platform bluesky --query "#politics" --query "#news" --limit 50

# Run coordination analysis on last 6 hours
purisa analyze --platform bluesky --hours 6

# Check for unusual coordination spikes
purisa spikes --platform bluesky

# View overall statistics
purisa stats
```

### Using the Web Dashboard

Open http://localhost:3000 to see:
- **Collection Panel**: Run data collection directly from the UI
- **Stats Cards**: Overview metrics for accounts, posts, and coordination
- **Platform Filter**: View data from specific platforms

### Understanding Results

**Coordination Score Interpretation:**

| Score | Meaning |
|-------|---------|
| 0-20 | Normal organic activity |
| 20-50 | Elevated coordination (may be natural) |
| 50-80 | High coordination (warrants investigation) |
| 80-100 | Very high coordination (likely campaign) |

**Spike Detection:**
- Spikes are hours where coordination exceeds 2+ standard deviations from baseline
- Use `purisa spikes` to see recent anomalies
- Higher z-score = more unusual activity

## CLI Commands

| Command | Description |
|---------|-------------|
| `purisa init` | Initialize database |
| `purisa collect` | Collect posts from platforms |
| `purisa analyze` | Run coordination detection |
| `purisa spikes` | Show coordination spikes |
| `purisa stats` | Display statistics |

**📖 Full CLI Documentation:** See [CLI_MANUAL.md](CLI_MANUAL.md)

## API Endpoints

### Health & Status
- `GET /api/health` - Health check
- `GET /api/platforms/status` - Available platforms

### Accounts & Posts
- `GET /api/accounts/all` - Get all accounts
- `GET /api/posts` - Get posts with filters

### Coordination (NEW in 2.0)
- `GET /api/coordination/metrics` - Get coordination metrics
- `GET /api/coordination/spikes` - Get coordination spikes
- `GET /api/coordination/timeline` - Get coordination timeline
- `GET /api/coordination/clusters` - Get detected clusters
- `POST /api/coordination/analyze` - Trigger coordination analysis
- `GET /api/coordination/stats` - Get coordination statistics

### Statistics
- `GET /api/stats/overview` - Overview statistics

### Manual Triggers
- `POST /api/collection/trigger` - Trigger collection
- `POST /api/analysis/trigger` - Trigger analysis

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
```

### Coordination Detection Settings

Defaults in `CoordinationConfig` (can be customized):

```python
sync_window_seconds: 90       # Synchronized posting window
text_similarity_threshold: 0.8  # TF-IDF similarity threshold
min_cluster_size: 3           # Minimum cluster size
min_cluster_density: 0.3      # Minimum density for clusters
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
```

2. Register in `backend/purisa/services/collector.py`
3. Add configuration to `platforms.yaml`

### Running Tests

```bash
cd backend
source venv/bin/activate
pytest
```

## Database

### SQLite (Development)
Default configuration uses SQLite (`purisa.db`)

### PostgreSQL (Production)

Update `DATABASE_URL` in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/purisa
```

## Roadmap

### Phase 1: MVP ✅
- ✅ Bluesky & Hacker News support
- ✅ 8 core detection signals
- ✅ Web dashboard
- ✅ CLI tool
- ✅ SQLite database

### Phase 2: Coordination Detection ✅ (Current)
- ✅ Network-based coordination analysis
- ✅ Cluster detection (Louvain algorithm)
- ✅ TF-IDF text similarity
- ✅ Hourly coordination scoring
- ✅ Spike detection
- ✅ Historical metrics storage
- 🔄 Dashboard redesign for timeline view

### Phase 3: Multi-Platform Expansion
- Mastodon integration
- Twitter/X integration (if access available)
- Reddit integration (if access available)
- Cross-platform correlation

### Phase 4: Visualization & UX
- Network graph visualization (D3.js)
- Coordination timeline views
- Spike investigation tools
- Export functionality (CSV, JSON)

### Phase 5: Production Ready
- PostgreSQL migration
- Docker containerization
- Cloud deployment guides
- Authentication system
- API rate limiting
- Automated testing
- CI/CD pipeline

## Troubleshooting

### "Platform not available" error
- Check that environment variables are set correctly
- For Bluesky: Verify handle and app password
- Run `purisa init` to verify configuration

### "Database not initialized" error
- Run `purisa init`
- Check `DATABASE_URL` in `.env`

### "No coordination detected"
This is normal for organic data! Coordination detection finds unusual patterns:
- Expect low scores (0-20) for natural activity
- Collect more data over time for better baselines
- Use `purisa spikes` to see anomalies

### Frontend can't connect to backend
- Verify backend is running on http://localhost:8000
- Check CORS settings in `backend/.env`
- Ensure both ports 3000 and 8000 are available

## Contributing

Contributions welcome! Please see CHANGELOG.md for current development status.

Areas we'd love help with:
- Additional platform adapters (Mastodon, Reddit, etc.)
- Network visualization
- Coordination detection algorithms
- Documentation
- Testing

## License

MIT License - see LICENSE file for details

## Acknowledgments

- **Bluesky Team**: For the open AT Protocol
- **Hacker News**: For the public API
- **NetworkX**: For graph analysis algorithms
- **FastAPI & React Communities**: For excellent frameworks

## Contact

For issues, questions, or contributions, please open an issue on GitHub.

---

**Note**: Purisa is a research and analysis tool. Coordination detection identifies patterns, not intent. Always interpret results in context and verify findings before drawing conclusions. High coordination scores may have legitimate explanations (e.g., news events, trending topics).
