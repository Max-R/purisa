# Purisa CLI Manual

Complete command-line interface reference for the Purisa 2.0 coordination detection system.

## Installation

### Quick Install

```bash
# Make install script executable
chmod +x install.sh

# Run installer
./install.sh
```

This creates a `purisa` command available system-wide.

### Manual Usage (Without Installing)

You can also run the CLI directly:

```bash
./purisa <command> [options]
```

Or the traditional way:

```bash
python3 cli.py <command> [options]
```

## Commands

### `purisa --help`

Show all available commands and global options.

```bash
purisa --help
```

---

### `purisa init`

Initialize the database and verify system configuration.

**Usage:**
```bash
purisa init
```

**What it does:**
- Creates SQLite database file (`purisa.db`)
- Initializes all tables (accounts, posts, coordination metrics, clusters)
- Verifies Bluesky credentials
- Checks platform availability

**Example output:**
```
Initializing Purisa...
Database URL: sqlite:///./purisa.db
✓ Database initialized
✓ Bluesky platform available
✓ Hacker News platform available
```

---

### `purisa collect`

Collect posts from social media platforms with real-time progress tracking.

**Usage:**
```bash
# Collect from specific platform with one query
purisa collect --platform <platform> --query "<search>" --limit <number>

# Collect from multiple queries (--query can be repeated)
purisa collect --platform <platform> --query "<query1>" --query "<query2>" --limit <number>

# Collect without comment harvesting
purisa collect --platform <platform> --query "<search>" --limit <number> --no-harvest-comments

# Run full collection cycle (uses config from platforms.yaml)
purisa collect
```

**Options:**
- `--platform` - Platform to collect from: `bluesky` or `hackernews`
- `--query` - Search query or hashtag (can be specified multiple times for batch collection)
- `--limit` - Number of posts to collect **per query** (default: 50)
- `--harvest-comments / --no-harvest-comments` - Enable/disable comment harvesting from top posts (default: enabled)

**Progress Tracking:**

The CLI displays progress bars when `tqdm` is available (installed by default):

```
Queries: 100%|████████████████████| 3/3 [00:15<00:00, current=#politics]
✓ Collected and stored 150 posts from 3 queries

Identifying top-performing posts...
  Posts qualifying: 12/150 (threshold: 0.01)

Harvesting comments from 12 top posts...
Harvesting comments: 100%|████████| 12/12 [00:08<00:00, comments=47]

✓ Harvested 47 comments from 12 top posts
```

**Bluesky Queries:**
- Hashtags: `#politics`, `#election2024`, `#climate`
- Keywords: `supreme court`, `legislation`, `senate`
- Mix: `#politics legislation`

**Hacker News Queries:**
- `top` - Top stories
- `new` - Newest stories
- `best` - Best stories
- `ask` - Ask HN posts
- `show` - Show HN posts

**Examples:**

```bash
# Collect 50 Bluesky posts about politics
purisa collect --platform bluesky --query "#politics" --limit 50

# Collect from multiple topics in one command (150 total posts)
purisa collect --platform bluesky --query "#politics" --query "#election2024" --query "#vote" --limit 50

# Collect environmental data from 3 hashtags (45 total posts)
purisa collect --platform bluesky --query "#climate" --query "#environment" --query "#sustainability" --limit 15

# Collect 30 top Hacker News stories
purisa collect --platform hackernews --query "top" --limit 30

# Collect from multiple platforms using config
purisa collect
```

---

### `purisa analyze`

Run coordination detection analysis on collected posts using network-based detection.

**Usage:**
```bash
# Analyze recent hours (default: 6 hours ending now)
purisa analyze --platform <platform>

# Analyze specific time range
purisa analyze --platform <platform> --hours <number> --start "<datetime>"

# Analyze all platforms
purisa analyze
```

**Options:**
- `--platform` - Platform to analyze: `bluesky` or `hackernews`
- `--hours` - Number of hours to analyze (default: 6)
- `--start` - Start time for analysis in ISO format (default: hours ago from now)

**What it does:**

For each hour in the analysis window:
1. Builds a similarity network between accounts based on:
   - **Synchronized posting** (posts within 90 seconds)
   - **URL sharing** (same links posted)
   - **Text similarity** (TF-IDF cosine similarity > 0.8)
   - **Hashtag overlap** (2+ shared hashtags)
   - **Reply patterns** (commenting on same posts)
2. Detects coordination clusters using Louvain community detection
3. Calculates hourly coordination score (0-100)
4. Stores metrics for historical tracking

**Coordination Score Components:**
- **Cluster Coverage** (40%): Percentage of posts from clustered accounts
- **Cluster Density** (30%): How tightly connected the clusters are
- **Sync Rate** (30%): Rate of synchronized posting

**Examples:**

```bash
# Analyze last 6 hours of Bluesky data
purisa analyze --platform bluesky

# Analyze last 24 hours
purisa analyze --platform bluesky --hours 24

# Analyze specific time range
purisa analyze --platform bluesky --hours 12 --start "2026-02-01T00:00:00"

# Analyze all platforms
purisa analyze
```

**Example output:**
```
=== Coordination Analysis ===
Platform: bluesky
Time range: 2026-02-01 22:00 to 2026-02-02 04:00
Hours to analyze: 6

Analyzing: 100%|██████████| 6/6 [00:00<00:00, clusters=9, score=49.9]

=== Analysis Summary ===
Hours analyzed: 6
Total posts: 88
Coordinated posts: 65
Clusters detected: 9
Average coordination score: 49.9/100
Peak coordination score: 100.0/100

=== High Coordination Hours (4) ===
  2026-02-02 01:00: score=100.0, clusters=5
  2026-02-02 02:00: score=100.0, clusters=2
  2026-02-02 00:00: score=65.0, clusters=2
  2026-02-01 22:00: score=26.7, clusters=0
```

---

### `purisa spikes`

Detect and display coordination spikes (unusual activity above baseline).

**Usage:**
```bash
# Show spikes from last 7 days
purisa spikes --platform <platform>

# Customize lookback period and threshold
purisa spikes --platform <platform> --hours <number> --threshold <std_devs>
```

**Options:**
- `--platform` - Platform to check: `bluesky` or `hackernews`
- `--hours` - Hours to look back (default: 168 = 7 days)
- `--threshold` - Standard deviations above mean to consider a spike (default: 2.0)

**What it does:**

1. Retrieves coordination metrics for the specified time period
2. Calculates baseline mean and standard deviation
3. Identifies hours where coordination score exceeds threshold
4. Displays spikes sorted by magnitude (z-score)

**Examples:**

```bash
# Show spikes from last 7 days (default)
purisa spikes --platform bluesky

# Show spikes from last 24 hours
purisa spikes --platform bluesky --hours 24

# More sensitive detection (1.5 std devs)
purisa spikes --platform bluesky --threshold 1.5

# Less sensitive detection (3.0 std devs)
purisa spikes --platform bluesky --threshold 3.0
```

**Example output:**
```
=== Coordination Spikes ===
Platform: bluesky
Looking back: 24 hours (1 days)
Threshold: 2.0 standard deviations

+------------------+---------+-------------+------------+---------+
| Time             |   Score | Magnitude   |   Clusters |   Posts |
+==================+=========+=============+============+=========+
| 2026-02-02T01:00 |     100 | 2.06σ       |          5 |      40 |
+------------------+---------+-------------+------------+---------+
| 2026-02-02T02:00 |     100 | 2.06σ       |          2 |      15 |
+------------------+---------+-------------+------------+---------+

Baseline: mean=23.0, std=37.3
```

---

### `purisa stats`

Show statistics and overview of collected data and coordination analysis.

**Usage:**
```bash
# Overall statistics
purisa stats

# Platform-specific statistics
purisa stats --platform <platform>
```

**Options:**
- `--platform` - Filter by platform: `bluesky` or `hackernews`

**Examples:**

```bash
# Show all statistics
purisa stats

# Show only Bluesky stats
purisa stats --platform bluesky
```

**Example output:**
```
=== Purisa 2.0 Statistics ===

Total Accounts: 1440
Total Posts: 2228
Total Clusters Detected: 9

=== Platform Breakdown ===

+------------+------------+---------+
| Platform   |   Accounts |   Posts |
+============+============+=========+
| bluesky    |         54 |      88 |
+------------+------------+---------+
| hackernews |       1386 |    2140 |
+------------+------------+---------+

=== Coordination (Last 24 Hours) ===

Hours analyzed: 20
Average coordination score: 15.0/100
Peak coordination score: 100.0/100
Coordinated posts detected: 65
Active clusters: 9
```

---

## Workflows

### Coordination Detection Workflow

1. **Initialize** (first time only)
   ```bash
   purisa init
   ```

2. **Collect Data**
   ```bash
   purisa collect --platform bluesky --query "#politics" --limit 100
   ```

3. **Run Coordination Analysis**
   ```bash
   purisa analyze --platform bluesky --hours 6
   ```

4. **Check for Spikes**
   ```bash
   purisa spikes --platform bluesky
   ```

5. **View Statistics**
   ```bash
   purisa stats
   ```

### Continuous Monitoring

```bash
# Collect fresh data
purisa collect --platform bluesky --query "#election2024" --limit 200

# Run coordination analysis
purisa analyze --platform bluesky --hours 24

# Check for unusual activity
purisa spikes --platform bluesky --hours 24

# Review statistics
purisa stats
```

### Multi-Platform Analysis

```bash
# Collect from Bluesky
purisa collect --platform bluesky --query "#AI" --limit 50

# Collect from Hacker News
purisa collect --platform hackernews --query "top" --limit 30

# Analyze all platforms
purisa analyze

# View combined statistics
purisa stats
```

---

## Tips & Best Practices

### Effective Queries

**Bluesky:**
- Use hashtags for topical content: `#politics`, `#technology`
- Combine multiple hashtags: `#AI #ethics`
- Use keywords for broader searches: `artificial intelligence`

**Hacker News:**
- `top` for most popular current stories
- `new` for real-time monitoring
- `ask` for community discussions

### Collection Limits

- **Small tests:** `--limit 20-50`
- **Regular monitoring:** `--limit 100-200`
- **Comprehensive analysis:** `--limit 500+`

### Understanding Coordination Scores

| Score Range | Interpretation |
|-------------|----------------|
| 0-20 | Normal organic activity |
| 20-50 | Elevated coordination (may be natural clustering) |
| 50-80 | High coordination (warrants investigation) |
| 80-100 | Very high coordination (likely coordinated campaign) |

### Spike Detection Thresholds

| Threshold | Sensitivity | Use Case |
|-----------|-------------|----------|
| 1.5σ | High | Catch subtle coordination |
| 2.0σ | Medium (default) | Balanced detection |
| 3.0σ | Low | Only major anomalies |

### Using Multiple Queries Effectively

The `--query` option can be specified multiple times to collect from different topics in a single command:

**Benefits:**
- **Efficiency:** Collect diverse data in one command instead of multiple runs
- **Topic Coverage:** Monitor related hashtags simultaneously
- **Batch Processing:** Authenticate once, collect from many sources

**Use Cases:**

1. **Related Topics:**
   ```bash
   # Collect across election-related hashtags
   purisa collect --platform bluesky \
     --query "#election2024" \
     --query "#vote" \
     --query "#politics" \
     --limit 100
   ```

2. **Broad Monitoring:**
   ```bash
   # Monitor multiple tech topics
   purisa collect --platform bluesky \
     --query "#AI" \
     --query "#technology" \
     --query "#innovation" \
     --query "#startup" \
     --limit 50
   ```

**Note:** The `--limit` applies **per query**, so `--query A --query B --limit 50` collects 100 total posts (50 from each).

### Database Management

```bash
# View database location
purisa init

# Backup database
cp backend/purisa.db backend/purisa_backup_$(date +%Y%m%d).db

# Reset database (WARNING: deletes all data)
rm backend/purisa.db
purisa init
```

---

## Configuration

### Environment Variables

Edit `backend/.env`:

```env
# Bluesky credentials
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_PASSWORD=your-app-password

# Database (default is fine)
DATABASE_URL=sqlite:///./purisa.db
```

### Coordination Detection Settings

Edit `backend/purisa/config/platforms.yaml` or use defaults:

```yaml
# Coordination detection thresholds (defaults)
coordination:
  sync_window_seconds: 90      # Posts within this window are "synchronized"
  text_similarity_threshold: 0.8  # Cosine similarity threshold
  min_cluster_size: 3          # Minimum accounts for a cluster
  min_cluster_density: 0.3     # Minimum edge density for clusters
```

---

## Troubleshooting

### "Command not found: purisa"

**Solution 1:** Run installer
```bash
chmod +x install.sh
./install.sh
```

**Solution 2:** Add to PATH manually
```bash
export PATH="$PATH:$HOME/.local/bin"
```

**Solution 3:** Use direct path
```bash
./purisa <command>
```

### "Platform not available"

Check credentials in `backend/.env`:
```bash
purisa init
```

### "Database not initialized"

Initialize the database:
```bash
purisa init
```

### "No data collected"

Verify:
1. Credentials are correct
2. Query is valid for the platform
3. Network connection is active

```bash
purisa collect --platform bluesky --query "#test" --limit 10
```

### "No coordination detected"

This is normal for organic data! Coordination detection finds unusual patterns. If your data is natural, expect:
- Low coordination scores (0-20)
- Few or no clusters detected
- No spikes above baseline

Try collecting more data or monitoring over a longer period.

---

## Advanced Usage

### Scripting

```bash
#!/bin/bash
# Automated coordination monitoring script

# Collect from multiple topics
for topic in politics technology science; do
    purisa collect --platform bluesky --query "#$topic" --limit 100
done

# Run coordination analysis
purisa analyze --platform bluesky --hours 24

# Check for spikes
purisa spikes --platform bluesky --hours 24

# Email results if spikes found
SPIKE_COUNT=$(purisa spikes --platform bluesky --hours 24 | grep -c "σ")
if [ "$SPIKE_COUNT" -gt 0 ]; then
    purisa spikes --platform bluesky --hours 24 | mail -s "Coordination Alert" admin@example.com
fi
```

### Cron Jobs

```cron
# Collect and analyze every 6 hours
0 */6 * * * cd /path/to/purisa && ./purisa collect && ./purisa analyze

# Daily spike report at 9 AM
0 9 * * * cd /path/to/purisa && ./purisa spikes --hours 168 | mail -s "Weekly Coordination Report" admin@example.com
```

---

## API Integration

The CLI works alongside the web API. You can:

1. **Collect via CLI, view via dashboard:**
   ```bash
   purisa collect --platform bluesky --query "#politics" --limit 200
   purisa analyze --platform bluesky
   # Then visit http://localhost:3000
   ```

2. **Get coordination metrics via API:**
   ```bash
   curl http://localhost:8000/api/coordination/metrics?platform=bluesky | jq .
   ```

3. **Get coordination spikes via API:**
   ```bash
   curl "http://localhost:8000/api/coordination/spikes?platform=bluesky&hours=168" | jq .
   ```

4. **Get coordination timeline:**
   ```bash
   curl "http://localhost:8000/api/coordination/timeline?platform=bluesky&hours=24" | jq .
   ```

5. **Trigger analysis programmatically:**
   ```bash
   curl -X POST "http://localhost:8000/api/coordination/analyze?platform=bluesky&hours=6"
   ```

---

## Getting Help

- **Command help:** `purisa <command> --help`
- **General help:** `purisa --help`
- **Documentation:** See README.md
- **Issues:** https://github.com/your-repo/purisa/issues

---

## Version

CLI Version: 2.0.0
Purisa Backend: FastAPI + SQLAlchemy + NetworkX + scikit-learn
Frontend: React 19 + shadcn/ui
Last Updated: 2026-02-01
