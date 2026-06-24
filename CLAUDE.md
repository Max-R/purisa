# Purisa — Project Context

Multi-platform coordination detection system (v2.1). Detects coordinated inauthentic behavior on Bluesky and Hacker News using network analysis. Includes cron-based job scheduling with live SSE updates.

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
│       │   ├── coordination_models.py  # ClusterDB, MetricDB, EdgeDB
│       │   └── job_models.py       # ScheduledJobDB, JobExecutionDB
│       ├── services/
│       │   ├── collector.py        # Data collection from platforms
│       │   ├── coordination.py     # CoordinationAnalyzer (NetworkX)
│       │   ├── similarity.py       # TF-IDF text similarity
│       │   ├── scheduler.py        # JobScheduler (cron-based, APScheduler)
│       │   ├── job_executor.py     # SSEEventBus + JobExecutor pipeline
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
│   │   │   ├── SchedulePanel.tsx   # Scheduled jobs CRUD + SSE status
│   │   │   ├── CronInput.tsx       # Cron expression builder
│   │   │   ├── JobHistory.tsx      # Execution history table
│   │   │   ├── CoordinationStatsCards.tsx  # Coordination stat cards
│   │   │   ├── CoordinationTimeline.tsx   # Recharts interactive timeline
│   │   │   ├── ClustersTable.tsx   # Detected clusters with expandable members
│   │   │   └── SpikesAlert.tsx     # Coordination spike alerts
│   │   ├── hooks/                  # useCoordination, useScheduledJobs, useJobEvents
│   │   │   └── types/coordination.ts  # Coordination API types
│   │   └── api/client.ts           # Axios API client (jobs + coordination)
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

- **Backend**: FastAPI + SQLAlchemy + NetworkX + scikit-learn + pandas + APScheduler
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
- **SSE route ordering**: `/api/jobs/events/stream` MUST be defined before `/api/jobs/{job_id}` in routes.py — otherwise FastAPI captures "events" as a job_id parameter
- **Scheduler accessor pattern**: `routes.py` uses `set_scheduler()`/`get_scheduler()` module-level functions to avoid circular imports — `main.py` calls `set_scheduler()` after creating the scheduler
- **JobExecutionDB no FK**: `job_id` column intentionally has no ForeignKey — execution history survives job deletion
- **APScheduler job IDs**: Use `purisa_job_{db_id}` naming convention, with `replace_existing=True`
- **Job model registration**: `connection.py` imports `job_models` (like `coordination_models`) to ensure tables are created
- **Job API uses JSON bodies**: POST/PUT `/api/jobs` accept Pydantic request bodies (not query params) — queries are sent as JSON arrays to avoid comma-splitting bugs
- **Lazy executor init**: `JobExecutor` uses `@property` for collector/analyzer to avoid blocking the event loop at startup (BlueskyPlatform does synchronous HTTP login)
- **Recharts**: Frontend uses `recharts` for interactive coordination timeline chart
- **source_query tracking**: `PostDB.source_query` stores which search query collected each post. Legacy posts (pre-tracking) have `NULL`. Lightweight migration in `connection.py` adds the column to existing databases.
- **Query-filtered coordination**: Timeline/clusters/stats endpoints accept optional `query` param. When provided, post counts come from PostDB (filtered), but coordination scores remain platform-wide (from CoordinationMetricDB).

## Git Workflow

All non-trivial changes must be done on a feature branch (`feature/<name>`) and merged via PR. Never commit directly to `main`.

```bash
git checkout -b feature/my-feature   # Create feature branch
# ... make changes ...
git push -u origin feature/my-feature
gh pr create --title "Add my feature" --body "..."
```

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
| GET | `/api/jobs` | List scheduled jobs |
| POST | `/api/jobs` | Create scheduled job (JSON body) |
| GET | `/api/jobs/events/stream` | SSE stream (live events) |
| GET | `/api/jobs/{id}` | Job detail |
| PUT | `/api/jobs/{id}` | Update job (JSON body) |
| DELETE | `/api/jobs/{id}` | Delete job |
| POST | `/api/jobs/{id}/run` | Manual trigger |
| GET | `/api/jobs/{id}/history` | Execution history |
| GET | `/api/coordination/queries?platform=X` | Distinct source queries with post counts |
