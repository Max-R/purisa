# Phase 0 — Validation Harness

Tests the **analytical hypothesis** from `VISION.md`: *structural coordination
signals reliably separate coordinated from organic collective behaviour.*

The lighthouse test: run the **unchanged** `CoordinationAnalyzer` against the
public [FiveThirtyEight / Clemson IRA troll-tweet dataset](https://github.com/fivethirtyeight/russian-troll-tweets)
(~3M tweets from ~2,800 labelled Internet Research Agency accounts, 2012-2018)
and measure whether it clusters known-coordinated accounts.

## What this measures (and what it can't)

The IRA dataset contains **only** troll accounts — no organic background. On its
own it measures **recall**: given accounts known to be coordinated, what fraction
does the engine place in a detected cluster?

It does **not** measure precision or false-positive rate. Those come from the
other Phase 0 legs (see Roadmap below):

- **Negative controls** — benign-but-busy communities (high volume, high text
  similarity, zero coordination intent). FPR = fraction of organic accounts flagged.
- **Synthetic injection** — inject N synthetic coordinated accounts into an
  organic stream, sweep thresholds, plot ROC.

## Isolation

Validation data never touches `purisa.db`:

- Separate database: `validation/ira.db` (gitignored via the global `*.db` rule)
- Distinct platform tag: `platform = "ira"` — the analyzer filters by platform,
  so even a shared DB would not cross-contaminate
- `source_query = "validation:ira"` on every row

## Usage

```bash
source backend/venv/bin/activate

# 1. Download the dataset (~600MB, 13 CSVs) into validation/data/
./validation/download_ira.sh

# 2. Load into validation/ira.db (excludes retweets from analysis by default)
python3 validation/load_ira.py

# 3. Run the analyzer over a window and compute recall
python3 validation/run_validation.py --start 2016-10-01T00:00 --end 2016-10-08T00:00
```

`load_ira.py` prints a posts-per-day density profile at the end — use it to pick
dense analysis windows (the Oct-Nov 2016 US election stretch is the obvious
first target). Analyzing all six years hour-by-hour (~50k hours) is pointless;
most hours are sparse.

For a quick smoke test before committing to the full load:

```bash
python3 validation/load_ira.py --limit-files 1
python3 validation/run_validation.py --auto-window
```

## Retweet handling (important)

A large share of dataset rows are retweets — verbatim copies that the TF-IDF
similarity detector (>0.8) clusters trivially, which would inflate recall.
`load_ira.py --retweet-mode` controls this:

| Mode | Behaviour |
|---|---|
| `exclude` *(default)* | Loaded with `post_type='retweet'` — stored for stats, **invisible to the analyzer** (it only reads `post_type='post'`). The honest recall number. |
| `include` | Loaded as `post_type='post'` — analyzer sees them. Use with a distinct `--platform-tag ira_rt` to compare. |
| `skip` | Not loaded at all. |

Report recall **with and without retweets**; the without-retweets number is the
one that means anything.

## Metric definitions

- **Account-level recall** = |eligible ∩ clustered| / |eligible|, where
  *eligible* = troll accounts with ≥K original posts inside the analyzed window
  (default K=3, matching `min_cluster_size`; reported for K ∈ {1, 3, 5}), and
  *clustered* = accounts appearing in any detected cluster in that window.
  The K floor keeps the denominator fair — an account that posted once in the
  window cannot honestly be counted as a miss.
- **Per-category recall** — the dataset labels accounts (RightTroll, LeftTroll,
  NewsFeed, HashtagGamer, NonEnglish, ...). NonEnglish behaviour under the
  TF-IDF tokenizer is a known question mark; per-category numbers surface it.

## Provenance & ethics notes

- The dataset was compiled by Clemson researchers (Linvill & Warren) from the
  official IRA handle lists Twitter provided to Congress, and published by
  FiveThirtyEight explicitly for public research. Validating coordination
  detectors against it is standard practice in the field.
- The repo has **no formal license**: use for internal validation is
  established norm, but **never redistribute the corpus** (hence `data/` is
  gitignored) or bundle it with Purisa.
- Treat the labels as **high-precision, unknown-recall** ground truth: every
  labelled account is a confirmed troll, but unlabelled coordinated accounts
  existed too. Recall claims are safe; precision claims need synthetic
  injection, where ground truth is perfect.
- **Never commit real-account results** to the repo (`results/` is gitignored);
  pseudonymize handles in anything shared outside the team. Coordination ≠
  guilt — see VISION.md guardrails.

## Known caveats

- **Timezone**: `publish_date` (`M/D/YYYY H:MM`) has no documented timezone; we
  assume UTC. This shifts hour buckets uniformly, so sync-window detection
  (90s) inside an hour is unaffected, but window boundary times are ±hours.
- **Account creation dates** are not in the dataset — `AccountDB.created_at`
  stays NULL. Follower/following counts are harvest-time snapshots (max kept).
- **Rows without a tweet_id** get a deterministic content-hash ID; re-loading is
  idempotent either way (`INSERT OR IGNORE` on primary key).

## Roadmap (Phase 0 legs)

- [x] IRA loader + recall harness (this scaffold)
- [x] Run + calibrate: recall numbers on dense windows, with/without retweets — see `RESULTS.md`
- [ ] Negative control: benign-but-busy organic corpus → false-positive rate
- [ ] Synthetic injection: threshold sweep → ROC for `sync_window_seconds`,
      `text_similarity_threshold`, `min_cluster_density`
- [ ] `REPORT.md` with the three headline metrics: recall, FPR, separation
