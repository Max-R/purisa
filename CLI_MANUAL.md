# Purisa CLI Manual

Complete command-line interface reference for the Purisa bot detection system.

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
- Initializes all tables (accounts, posts, scores, flags)
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

If `tqdm` is not available, text-based progress updates are shown instead.

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

**What it does:**
1. Fetches posts matching your query
2. Retrieves account info for each post author
3. Stores posts and accounts in database
4. Handles duplicates automatically

**Comment Harvesting:**

When `--harvest-comments` is enabled (default), the CLI:
1. Identifies top-performing posts based on engagement score
2. Shows stats: qualifying posts, threshold, and any capping
3. Harvests comments with a progress bar
4. Fetches full profiles for commenter accounts
5. Runs inflammatory content detection (Detoxify ML)

**Top Performer Stats:**

The CLI shows detailed stats about which posts qualify for comment harvesting:
- `Posts qualifying`: How many posts meet the engagement threshold
- `Threshold`: The minimum engagement score (configurable in platforms.yaml)
- `Capped at`: If more posts qualify than the max limit, shows how many were skipped

---

### `purisa analyze`

Analyze accounts for bot-like behavior using 13 detection signals.

**Usage:**
```bash
# Analyze all accounts
purisa analyze

# Analyze specific account
purisa analyze --account <account-id> --platform <platform>

# Analyze all accounts from one platform
purisa analyze --platform <platform>
```

**Options:**
- `--account` - Specific account ID (DID for Bluesky, username for HN)
- `--platform` - Filter by platform: `bluesky` or `hackernews`

**Examples:**

```bash
# Analyze all collected accounts
purisa analyze

# Analyze specific Bluesky account
purisa analyze --account did:plc:abc123xyz --platform bluesky

# Analyze only Hacker News accounts
purisa analyze --platform hackernews
```

**Core Detection Signals (0-13.5 max):**
1. **New Account** (0-2): Recently created accounts
2. **High Frequency** (0-3): Impossibly high posting rates
3. **Repetitive Content** (0-2.5): Duplicate or near-duplicate posts
4. **Low Engagement** (0-1.5): High volume, low interaction
5. **Generic Username** (0-1): Bot-like username patterns
6. **Incomplete Profile** (0-1): Missing bio, avatar, etc.
7. **Temporal Patterns** (0-1): 24/7 posting behavior
8. **Unverified Account** (0-1.5): Lacks verification or trust signals

**Comment-Based Signals (0-8.5 max):**
9. **Inflammatory Content** (0-3): Toxic/hateful comments (Detoxify ML)
10. **Comment Frequency** (0-2): High-volume comment activity
11. **Comment Timing** (0-1.5): Rapid replies to viral content
12. **Comment Repetition** (0-1): Copy-paste comments
13. **Low Quality Comments** (0-1): Generic/spammy comment patterns

**Total Maximum Score: 22.0**

**Threshold:** Accounts scoring ≥7.0 are flagged as suspicious.

**Note:** Verified Bluesky accounts (blue checkmark) and high-karma HN users (≥1000) receive 0 points for the unverified signal, reducing their overall bot score.

**Progress Tracking:**

The CLI displays a progress bar during analysis:

```
Analyzing all accounts...
Analyzing: 100%|████████████████████| 156/156 [00:12<00:00, flagged=12]

✓ Analyzed 156 accounts
  Flagged: 12
  Clean: 144
```

**Example output (without tqdm):**
```
Analyzing all accounts...
  Progress: 20/156 accounts, 2 flagged
  Progress: 40/156 accounts, 4 flagged
  ...
✓ Analyzed 156 accounts
  Flagged: 12
  Clean: 144
```

---

### `purisa flagged`

Display accounts flagged as bots.

**Usage:**
```bash
# Show flagged accounts (default: first 20)
purisa flagged

# Show all flagged accounts
purisa flagged --all

# Filter by platform
purisa flagged --platform <platform>
```

**Options:**
- `--platform` - Filter by platform: `bluesky` or `hackernews`
- `--all` - Show all results (no limit)

**Examples:**

```bash
# Show first 20 flagged accounts
purisa flagged

# Show all flagged accounts
purisa flagged --all

# Show only flagged Bluesky accounts
purisa flagged --platform bluesky
```

**Example output:**
```
=== Flagged Accounts ===

Found 3 suspicious accounts:

+-------------------------+----------+-------+-------+-----------+
| Username                | Platform | Score | Posts | Followers |
+=========================+==========+=======+=======+===========+
| bot_news_247.bsky.social| bluesky  |  8.5  |  156  |    12     |
+-------------------------+----------+-------+-------+-----------+
| auto_poster             | bluesky  |  7.8  |  203  |     5     |
+-------------------------+----------+-------+-------+-----------+
| news_aggregator_bot     | bluesky  |  7.2  |   89  |     0     |
+-------------------------+----------+-------+-------+-----------+
```

---

### `purisa stats`

Show statistics and overview of collected data.

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
=== Purisa Statistics ===

Total Accounts: 156
Total Posts: 432
Flagged Accounts: 12
Flag Rate: 7.7%

=== Platform Breakdown ===

+------------+------------+---------+
| Platform   |   Accounts |   Posts |
+============+============+=========+
| bluesky    |        142 |     398 |
+------------+------------+---------+
| hackernews |         14 |      34 |
+------------+------------+---------+
```

---

## Workflows

### Basic Bot Detection Workflow

1. **Initialize** (first time only)
   ```bash
   purisa init
   ```

2. **Collect Data**
   ```bash
   purisa collect --platform bluesky --query "#politics" --limit 100
   ```

3. **Analyze for Bots**
   ```bash
   purisa analyze
   ```

4. **View Results**
   ```bash
   purisa flagged
   purisa stats
   ```

### Continuous Monitoring

```bash
# Collect fresh data
purisa collect --platform bluesky --query "#election2024" --limit 200

# Analyze new accounts
purisa analyze --platform bluesky

# Check for new bots
purisa flagged --platform bluesky

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

3. **Cross-Topic Analysis:**
   ```bash
   # Environmental and policy intersection
   purisa collect --platform bluesky \
     --query "#climate" \
     --query "#policy" \
     --query "#legislation" \
     --limit 75
   ```

**Note:** The `--limit` applies **per query**, so `--query A --query B --limit 50` collects 100 total posts (50 from each).

### Reducing False Positives

- Collect more posts per account (higher `--limit`)
- Run analysis multiple times over days/weeks
- Manually review high-scoring accounts
- Adjust thresholds in `backend/.env`

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
# Detection thresholds
BOT_DETECTION_THRESHOLD=7.0    # Flag threshold (0-10)
NEW_ACCOUNT_DAYS=30            # Days to consider "new"
HIGH_FREQUENCY_THRESHOLD=50    # Posts per hour

# Bluesky credentials
BLUESKY_HANDLE=your-handle.bsky.social
BLUESKY_PASSWORD=your-app-password
```

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

---

## Advanced Usage

### Scripting

```bash
#!/bin/bash
# Automated bot detection script

# Collect from multiple topics
for topic in politics technology science; do
    purisa collect --platform bluesky --query "#$topic" --limit 100
done

# Analyze everything
purisa analyze

# Email results (requires mail setup)
purisa flagged --all > flagged_accounts.txt
mail -s "Bot Detection Report" admin@example.com < flagged_accounts.txt
```

### Cron Jobs

```cron
# Run every 6 hours
0 */6 * * * cd /path/to/purisa && ./purisa collect && ./purisa analyze

# Daily summary at 9 AM
0 9 * * * cd /path/to/purisa && ./purisa stats | mail -s "Daily Bot Stats" admin@example.com
```

---

## API Integration

The CLI works alongside the web API. You can:

1. **Collect via CLI, view via dashboard:**
   ```bash
   purisa collect --platform bluesky --query "#politics" --limit 200
   # Then visit http://localhost:3000
   ```

2. **Trigger collection via API:**
   ```bash
   # Collect with query and harvest comments
   curl -X POST "http://localhost:8000/api/collection/trigger?platform=bluesky&query=%23politics&limit=100&harvest_comments=true"
   ```

3. **Trigger analysis programmatically:**
   ```bash
   curl -X POST http://localhost:8000/api/analysis/trigger
   ```

4. **Export data:**
   ```bash
   curl http://localhost:8000/api/accounts/flagged | jq . > flagged.json
   ```

5. **Get comment statistics:**
   ```bash
   curl http://localhost:8000/api/stats/comments | jq .
   ```

---

## Getting Help

- **Command help:** `purisa <command> --help`
- **General help:** `purisa --help`
- **Documentation:** See README.md
- **Issues:** https://github.com/your-repo/purisa/issues

---

## Version

CLI Version: 1.0.0
Purisa Backend: FastAPI + SQLAlchemy + Detoxify ML
Frontend: React 19 + shadcn/ui
Last Updated: 2026-01-26
