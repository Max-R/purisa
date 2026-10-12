# Phase 0 — Run + Calibrate Results (IRA recall)

First full run of the recall harness against the FiveThirtyEight/Clemson IRA
corpus, 2026-07-08. Unchanged production `CoordinationAnalyzer`, default config
(90s sync window, TF-IDF >0.8, Louvain min size 3 / density 0.3). Aggregate
numbers only — per-account results stay in `validation/results/` (gitignored).

## Corpus

2,843 accounts · 1,648,625 original posts · 1,297,582 retweets (loaded as
`post_type='retweet'`, invisible to the analyzer). Density surprise: the
densest stretch is **August 2017 (Charlottesville week)**, not the Oct–Nov
2016 election run — Aug 12–18 2017 all exceed 9,900 analyzer-visible
posts/day.

## Headline recall (account-level, K = min posts in window)

| Window | Density | K≥1 | K≥3 | K≥5 |
|---|---|---|---|---|
| 2017-08-12 → 08-19 (Charlottesville wk) | ~470 posts/hr | 99.6% (234/235) | 99.5% (215/216) | 100% (201/201) |
| 2016-10-01 → 10-08 (pre-election wk) | ~53 posts/hr | 98.6% (214/217) | 100% (181/181) | 100% (161/161) |
| 2015-09-16 (median-density day) | ~34 posts/hr | 87.5% (77/88) | 97.4% (37/38) | 100% (27/27) |
| 2018-01-01 → 01-08 (sparse tail wk) | ~few posts/hr | 60.0% (6/10) | 85.7% (6/7) | 85.7% (6/7) |

With retweets included (`ira_rt` tag): Aug 2017 wk K≥3 = 99.6% (271/272),
Oct 2016 wk K≥3 = 100% (296/296). **The honest (no-retweet) number matches
the inflated one** — recall does not depend on verbatim-copy clustering.

Per-category (K≥3, both headline weeks): RightTroll, NewsFeed, HashtagGamer,
Fearmonger 100%; LeftTroll 80–100% (small n); **NonEnglish 96–100%** — the
TF-IDF tokenizer question mark from the README resolves benignly, because
sync/URL/hashtag edges carry non-English accounts even if text similarity
underperforms.

## Calibration findings

1. **The sync channel saturates.** Median `sync_rate` = 1.0 in *every*
   analyzed window, even at 53 posts/hr (median gap ~68s < 90s window). On a
   troll-only corpus at any realistic density, the 90s sync detector alone
   wires the whole graph — recall here is necessary but cheap. Text
   similarity flags a median of only ~6% of posts and is doing the real
   discriminating work. Consequence: **the FPR leg (negative controls) is
   the load-bearing test**; a busy organic community will also saturate
   sync_rate, and only the threshold sweep will show whether the composite
   score separates them.
2. **Recall degrades where it honestly should.** Misses concentrate in
   sparse windows among accounts with 1–2 posts (no structural signal
   exists). K≥3 recall stays ≥97% down to median density; the sparse 2018
   tail (agency winding down) drops to 85.7% on n=7.
3. **Coordination scores sit high**: hourly median 85–89 (min 46.7) across
   both headline weeks — consistent with a corpus that is coordinated by
   construction.

## Bug found by this run

Cross-platform `cluster_id` collision: IDs were minted from
`time_window_start` only, while the DB column is globally unique — two
platforms analyzing the same hour collided and the second platform's
clusters were **silently dropped** (caught + logged). Surfaced when `ira`
and `ira_rt` shared `validation/ira.db`; would equally hit bluesky + HN in
production. Fixed by prefixing the platform
(`{platform}_{window}_cluster_{i}`); re-analysis cleanup queries by
platform + window, so no migration needed. Verified: same-day re-run under
both tags stores cleanly.

## What this does not show

Recall only. Precision / false-positive rate requires the negative-control
and synthetic-injection legs (see README roadmap). Treat these numbers as
"the engine does not miss dense coordinated behaviour", not "the engine can
tell it apart from organic behaviour".

## Addendum 2026-09-22 (feature/phase0-fixes)

### Determinism bug and fix

Results were not reproducible across processes. `louvain_communities()` was
seeded (`seed=42`), but Louvain's output also depends on node and adjacency
insertion order, and the graph was built by iterating sets of account IDs and
detector output whose order follows Python's per-process string-hash
randomisation. Measured: the 12:00 hour on 2015-09-16 gave **5 / 3 / 3 / 4
clusters under `PYTHONHASHSEED` 0 / 1 / 2 / 3**.

Fix: `_build_network` now returns a canonical graph with nodes and edges
inserted in sorted order (`_canonical_graph`); sync-pair detection breaks
same-timestamp ties by post ID; URL-pair and cluster-member output are
sorted. After the fix the same hour gives **3 clusters in every run**, and the
full-day metrics JSON is **byte-identical across four hash seeds**.

### Regenerated numbers (fixed engine, default config)

| Window | K≥1 | K≥3 | K≥5 | Clusters | Sizes min / median / mean / max | Largest cluster | Single-category |
|---|---|---|---|---|---|---|---|
| 2015-09-16 (day) | 87.5% (77/88) | 97.4% (37/38) | 100% (27/27) | 69 | 3 / 4 / 4.59 / 9 | 11.7% | 11/69 |
| 2016-10-01 → 10-08 (wk) | 98.6% (214/217) | 100% (181/181) | 100% (161/161) | 685 | 3 / 6 / 6.47 / 24 | 11.2% | 85/685 |

Recall is unchanged in both windows. The Oct 2016 week's 685 clusters were
reported as 695 in July — the difference is process noise from the bug above,
not a change in behaviour. "Largest cluster" is the share of distinct
clustered accounts sitting in the single largest cluster, so neither window's
recall rests on one giant cluster.

The Aug 2017 and Jan 2018 windows were **not re-run**; their cluster counts
under the fixed engine may differ by a few from any earlier figures. Recall is
unaffected by the fix.

### Threshold sweep (2015-09-16, seeds 42 and 7)

One parameter varied at a time around the defaults:

| Setting | K≥1 | K≥3 | K≥5 | Clusters |
|---|---|---|---|---|
| sync 10 s, 30 s | 50.0% | 76.3% | 92.6% | 38 |
| sync 60 s, 90 s (default) | 87.5% | 97.4% | 100% | 69 |
| sync 300 s | 98.9% | 100% | 100% | 67–69 |
| text threshold 0.7 / 0.8 / 0.9 | 87.5% | 97.4% | 100% | 69 |
| min density 0.5 | 65.9% | 94.7% | 100% | 58–60 |

Seeds 42 and 7 differ by only 1–2 clusters in any row and never in recall.
The sweep was run *before* the determinism fix, so the 1–2 cluster spread
mixes seed variation with the process noise described above; re-run it to
separate the two.

Interpretation: **the sync window dominates** recall on this corpus, and the
text threshold is inert here. The 10 s / 30 s rows are an artefact —
`publish_date` has minute resolution, so any sub-60 s window only sees
same-minute pairs, which is why 10 s and 30 s are identical (see the README's
minute-resolution caveat). They say nothing about the detector at those
windows.

### Purity and separation

n/a on IRA: there are no control accounts, so there is no negative class.
Both will be populated by the NIS / OSoMe legs (see README, "Datasets and
licences").
