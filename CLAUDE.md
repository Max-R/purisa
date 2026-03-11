# Purisa — Project Context

Multi-platform coordination detection system (v2.0). Detects coordinated inauthentic behavior on Bluesky and Hacker News using network analysis.

## Quick Start

```bash
./start.sh          # Backend :8000 + Frontend :3000
./stop.sh           # Kill all servers
```

- Dashboard: http://localhost:3000
- API docs: http://localhost:8000/docs

## Development Setup

```bash
# Backend (Python 3.12)
cd backend
source venv/bin/activate
pip install -r requirements.txt

# Frontend (Bun + React 19)
cd frontend
bun install

# Credentials
cp backend/.env.example backend/.env
# Add BLUESKY_HANDLE and BLUESKY_PASSWORD
```

**Use `backend/venv/` (Python 3.12).** A legacy `venv/` (Python 3.9) exists at project root — ignore it.

## Project Structure

```
purisa/
├── cli.py                          # CLI entry point (adds backend/ to sys.path)
├── start.sh / stop.sh              # Server orchestration
├── backend/
│   ├── .env                        # Credentials (gitignored)
│   ├── venv/                       # Python 3.12 virtualenv
│   └── purisa/
│       ├── main.py                 # FastAPI app
│       ├── api/routes.py           # All API endpoints
│       ├── config/
│       │   ├── settings.py         # Pydantic settings (reads .env)
│       │   └── platforms.yaml      # Platform targets and thresholds
│       ├── database/
│       │   ├── connection.py       # DB init, singleton pattern
│       │   ├── models.py           # AccountDB, PostDB, ScoreDB
│       │   └── coordination_models.py  # ClusterDB, MetricDB, EdgeDB
│       ├── services/
│       │   ├── collector.py        # Data collection from platforms
│       │   ├── coordination.py     # CoordinationAnalyzer (NetworkX)
│       │   ├── similarity.py       # TF-IDF text similarity
│       │   └── analyzer.py         # Legacy bot scorer (13 signals)
│       └── platforms/
│           ├── base.py             # Abstract adapter
│           ├── bluesky.py          # AT Protocol via atproto
│           └── hackernews.py       # Firebase API via httpx
├── frontend/
│   ├── src/
│   │   ├── index.tsx               # React entry
│   │   ├── App.tsx                 # Main dashboard
│   │   ├── components/             # UI components (shadcn/ui)
│   │   ├── hooks/                  # useStats, useAccounts
│   │   └── api/client.ts           # Axios API client
│   └── package.json
└── purisa.db                       # SQLite database (gitignored)
```

## CLI Commands

The `purisa` wrapper script activates `backend/venv` automatically.

| Command | Example |
|---------|---------|
| `purisa init` | Initialize database |
| `purisa collect` | `purisa collect --platform bluesky --query "#politics" --limit 100` |
| `purisa analyze` | `purisa analyze --platform bluesky --hours 6` |
| `purisa spikes` | `purisa spikes --platform bluesky --threshold 2.0` |
| `purisa stats` | Overview of accounts, posts, coordination metrics |

When running without the wrapper: `source backend/venv/bin/activate && python3 cli.py <command>`

## Architecture

- **Backend**: FastAPI + SQLAlchemy + NetworkX + scikit-learn + pandas
- **Frontend**: React 19 + Bun (native dev server, no Vite) + shadcn/ui + TailwindCSS
- **Database**: SQLite (`purisa.db` at project root), PostgreSQL-ready
- **CLI**: `cli.py` inserts `backend/` into `sys.path` and loads `backend/.env` via python-dotenv

### Coordination Detection Flow

1. Collect posts → `UniversalCollector` stores to `PostDB`
2. `CoordinationAnalyzer.analyze_hour()` builds NetworkX graph per hour
3. Edges created from: sync posting (90s window), URL sharing, TF-IDF similarity (>0.8), hashtag overlap, reply patterns
4. Louvain community detection → clusters (min size 3, min density 0.3)
5. Coordination score (0-100) stored in `CoordinationMetricDB`
6. Spike detection via MAD (Median Absolute Deviation) analysis (default: 2.0 threshold, min 24 samples)

## Known Gotchas

- **SQLAlchemy `metadata` reserved**: Columns named `cluster_metadata`, `metric_metadata`, `event_metadata` instead
- **Two venvs**: Use `backend/venv/` (3.12), not root `venv/` (3.9 legacy)
- **CLI .env loading**: `cli.py` lines 20-24 explicitly load `backend/.env` via dotenv — needed because CLI runs from project root
- **cluster_id**: Uses `time_window_start.strftime()` not `datetime.now()` — enables idempotent re-analysis
- **Coordination model registration**: `connection.py` imports `coordination_models` to ensure tables are created
- **Louvain determinism**: `seed=42` in `louvain_communities()` ensures reproducible cluster detection
- **AccountEdgeDB**: Populated by `_store_results()` — edges are written per analysis run (old edges deleted first for idempotency)
- **Rate clamping**: `sync_rate`, `url_rate`, `text_rate` are clamped to [0.0, 1.0] in `_calculate_metrics()`
- **Tailwind**: Must be compiled separately — `start.sh` runs `bunx tailwindcss` in watch mode alongside Bun dev server

## Testing

No automated tests yet. Manual verification:

```bash
source backend/venv/bin/activate
python3 cli.py init
python3 cli.py collect --platform bluesky --query "#test" --limit 10
python3 cli.py analyze --platform bluesky --hours 1
python3 cli.py spikes --platform bluesky
python3 cli.py stats
```

## Key API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/api/coordination/metrics?platform=X&hours=24` | Coordination scores |
| GET | `/api/coordination/spikes?platform=X&hours=168` | Spike detection |
| GET | `/api/coordination/timeline?platform=X&hours=24` | Timeline data |
| GET | `/api/coordination/clusters?platform=X` | Detected clusters |
| POST | `/api/coordination/analyze?platform=X&hours=6` | Trigger analysis |
| POST | `/api/collection/trigger?platform=X&query=Y` | Trigger collection |
