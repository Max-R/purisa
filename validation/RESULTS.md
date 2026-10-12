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
