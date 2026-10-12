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

Each run writes `validation/results/metrics_<tag>_<start>_<end>_<confighash>.json`
(pass `--output` to override). `<confighash>` is the first 8 hex chars of a
SHA-1 over the full `CoordinationConfig` (including `louvain_seed`), so runs
over the same window under different configs or seeds no longer overwrite each
other (issue #13); the config itself is recorded under
`generated_for.analyzer_config` in the JSON.

### Threshold sweep

```bash
cp validation/ira.db validation/ira_sweep.db
python3 validation/run_validation.py --db validation/ira_sweep.db \
    --start 2015-09-16 --end 2015-09-17 --sweep --seeds 42,7
```

`--sweep` varies one parameter at a time around the defaults
(`sync_window_seconds` 10/30/60/90/300, `text_similarity_threshold`
0.7/0.8/0.9, `min_cluster_density` 0.2/0.3/0.5), repeating each config once
per seed in `--seeds`, and writes `sweep_<tag>_<start>_<end>.json`. Without
`--sweep`, `--seeds` takes exactly one value (default 42).

**Sweeps rewrite stored clusters.** Every analysis run replaces the clusters,
edges and metrics stored for the windows it analyses, so after a sweep the DB
holds whichever config ran last. The harness therefore refuses `--sweep`
unless the `--db` filename contains `sweep` or `copy` (issue #18); pass
`--allow-rewrite` to override deliberately.

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
- **Cluster size stats** — count, min / median / mean / max members, and
  `largest_cluster_share` = size of the run's largest cluster / distinct
  clustered accounts. "In any cluster" is a generous hit criterion; one giant
  cluster would make recall trivial, and these numbers show whether it did.
- **Purity** — an account is *control* when
  `AccountDB.platform_metadata['is_control']` is truthy, otherwise
  *coordinated*. Cluster purity = coordinated members / members; reported as
  mean purity, share of clusters with purity ≥ 0.9, and control accounts
  clustered / total (false positives). **Null on IRA**: every account is a
  troll, so there is no negative class.
- **Per-category co-clustering** — number and share of clusters whose
  coordinated members all carry one category. Control accounts are excluded
  from the category set, so padding a troll cluster with controls (or an
  all-control cluster) cannot pass as single-category.
- **Separation** (issue #14) — account-level
  `participation = windows_clustered / windows_active`, where
  *windows_active* = hourly windows in the analysed range in which the account
  has ≥1 analyzer-visible post, and *windows_clustered* = those in which it
  sits in a detected cluster. Separation = ROC-AUC of participation,
  coordinated (positive) vs control (negative), with the KS statistic as a
  secondary number. Reported for K≥3 (headline) and K≥1, where **this K
  counts active windows, not posts** — it is not the recall K. **Null until a
  dataset with control accounts is loaded**; on IRA it is always n/a.

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
- **Minute resolution**: `publish_date` carries no seconds, so every gap
  between posts is a whole number of minutes. Any sync window under 60 s
  therefore only catches same-minute pairs, and all such windows (10 s, 30 s,
  ...) behave identically — the timestamps cannot express the difference. The
  10 s and 30 s sweep rows measure the timestamp format, not the detector;
  treat them as meaningless on IRA.
- **Determinism**: results used to vary from process to process for the same
  window — Louvain's output depends on node/edge insertion order, and Python's
  per-process string-hash randomisation reordered them despite `seed=42`.
  Fixed on `feature/phase0-fixes` by inserting nodes and edges in sorted order
  (`CoordinationAnalyzer._canonical_graph`); see the addendum in `RESULTS.md`.
- **Every run rewrites stored clusters** (and edges and metrics) for the
  analysed windows in whichever DB `--db` points at — not just sweeps. Point
  it at `purisa.db` and it will overwrite production analysis for those hours.

## Datasets and licences

Issue #15. Researched 2026-09-22; not legal advice. Summary of the terms for
the two datasets planned for the precision leg.

### OSoMe / Seckin et al., "Labeled Datasets for Research on Information Operations"

- **Where**: Zenodo concept record `10.5281/zenodo.14141549`, with 28 version
  DOIs — one per campaign plus "Main" (`10.5281/zenodo.14189193`, README and
  index). Paper: arXiv 2411.10609; ICWSM 2025.
- **Licence**: CC BY-NC-ND 4.0.
- **Access**: restricted, request-based. Under the data-sharing policy updated
  2026-09-09, requesters must be faculty, research staff or graduate students
  at a recognised research institution, applying from an institutional email
  address. The access terms allow **one data file per researcher per day**.
- **Labels**: `is_control` is **True for control accounts, False for IO
  accounts** (note the polarity). Account IDs, post IDs, URLs and usernames
  are one-way hashed.
- **What we may do**: use the files locally for non-commercial validation
  once access is granted; publish aggregate metrics (recall, precision, FPR,
  separation) with a citation to the paper; commit a loader that reads files
  the user obtained themselves, tested on **synthetic fixtures only**. **Never
  publish per-account output such as lists of hashed IDs** — that is sharing
  Adapted Material, which ND forbids. Never automate around Zenodo's access
  gate.

### South Korea NIS 2012 (Keller, Schoch, Stier & Yang)

- **Where**: OSF project `10.17605/OSF.IO/TPA6U`. Public, no login.
- **Licence**: none declared (`node_license: null`), so all rights reserved
  by default; no licence to redistribute.
- **Contents used**: `nis_tweets.csv` has `user_id`, `user_name` and `date`
  only — 702 unique accounts, ~194k rows, **no tweet text and no tweet IDs**.
  Only timing and account-level signals (sync, co-activity) are testable;
  text, URL and hashtag channels are not.
- **What we may do**: a loader that fetches from OSF **at runtime**, with
  retry and backoff on HTTP 429 (OSF rate-limits after roughly ten requests).
  Never commit the account list or anything derived from it. Cite Keller et
  al. 2020 (*Political Communication* 37(2)) with any published number.

**Status**: the OSoMe access request is to be submitted as an independent
civic-research project. While it is pending, the precision leg proceeds on
NIS + Bluesky organic controls + synthetic injection.

## Roadmap (Phase 0 legs)

- [x] IRA loader + recall harness (this scaffold)
- [x] Run + calibrate: recall numbers on dense windows, with/without retweets — see `RESULTS.md`
- [x] Cluster purity metric (control accounts via `platform_metadata['is_control']`)
- [x] Separation metric (participation ROC-AUC / KS) — implemented; n/a until
      a dataset with controls is loaded
- [x] Threshold sweep harness (`--sweep`, `--seeds`) — see `RESULTS.md` addendum
- [ ] Submit OSoMe access request
- [ ] NIS loader (runtime OSF fetch, no committed data)
- [ ] Negative control: benign-but-busy organic corpus → false-positive rate
- [ ] Synthetic injection: threshold sweep → ROC for `sync_window_seconds`,
      `text_similarity_threshold`, `min_cluster_density`
- [ ] `REPORT.md` with the three headline metrics: recall, FPR, separation
