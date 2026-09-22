# Purisa — Vision

*The strategy of record. Living document. Last updated 2026-09-22.*

Purisa began as a coordination-detection system for Bluesky and Hacker News. This
document records its evolution into a **collective-behaviour observatory**: one
configurable platform that answers a single question across many phenomena —
**"Is this real, or is it engineered?"**

---

## 1. Value statement (north star)

> **Purisa makes the hidden machinery of online influence visible — so researchers,
> journalists, and watchdogs can tell a genuine public outcry from a manufactured one,
> before a false narrative hardens into accepted truth.**

One-liner: *"Is this real, or is it engineered?" — answered with evidence, not vibes.*

**Positioning:** a rigorous, reproducible, **neutral core** with **watchdog framing**.
The engine measures; it does not editorialize. The presentation serves accountability.
Every claim the tool surfaces must be defensible enough to publish.

---

## 2. Who it serves

| Persona | Pain today | What Purisa gives them |
|---|---|---|
| **Disinformation researcher** (academic / lab) | Manual, un-reproducible coordination analysis | A reproducible, scored engine across platforms |
| **Investigative journalist** | "This *feels* like a brigade" — but no evidence to publish | A defensible organic-vs-coordinated measurement |
| **Civil-society / election monitor** | Can't afford a data-science team | Presets that work without writing code |

Shared need: a **defensible organic-vs-coordinated measurement they didn't have to
compute themselves.**

---

## 3. User stories

Each phenomenon shares one spine — *organic or engineered?*

- **Pile-on** — *As an investigative journalist, when a person is suddenly engulfed by
  thousands of hostile posts, I want to know whether it's an organic public reaction or
  a coordinated brigade — so I can report the truth instead of amplifying a manufactured
  mob.*
- **Disinformation** — *As a disinfo researcher, when a claim spreads explosively, I want
  to see whether one narrative is being pushed by a coordinated cluster — so I can
  attribute a campaign before it's accepted as fact.*
- **Political sentiment** — *As an election monitor, when sentiment toward a candidate
  shifts overnight, I want to know whether real voters moved or a coordinated network
  manufactured the swing — so I can flag interference in time.*

Coordinated inauthentic behaviour (CIB) and pump-&-dump hype are the same shape with
the structural detectors alone — they need no semantic layer.

---

## 4. The two hypotheses

These validate differently — keep them separate.

1. **Analytical hypothesis** — *Structural coordination signals reliably separate
   coordinated from organic collective behaviour, across domains.* (Does the engine
   work?)
2. **Product hypothesis** — *Researchers and journalists will trust and act on a
   structural-coordination score, with its evidence, that they didn't compute
   themselves.* (Does anyone care?)

**Analytical correctness leads.** For a civic tool, a wrong answer doesn't just lose a
sale — it manufactures a false accusation. Credibility is the product. We test the
engine before we sell the story.

---

## 5. The differentiator

The **structural-coordination axis** — the thing pure sentiment tools cannot measure,
because they lack a graph layer:

- Many people **independently** angry → high volume, **low** inter-account coordination.
- An organised **brigade** → high volume, **high** coordination (synchronised timing,
  shared copypasta/links, clustered account creation).

Purisa plots a pile-on on that axis. The same measurement separates grassroots political
sentiment from astroturfed sentiment. This is the moat.

**What the axis is not** (decision 2026-09-22, from the literature review in
`docs/research/2026-09-22-cib-state-of-the-art.md`): the field now treats
*coordination*, *authenticity* and *harm* as orthogonal. Activists, fandoms, newsrooms
and campaign volunteers coordinate authentically and light up every structural signal
we have; detectors run on Facebook surfaced *predominantly* media groups, activists and
ad networks. So the axis is labelled **"low ↔ high structural coordination"**, never
"organic ↔ engineered". Whether a highly coordinated cluster is a movement or a machine
is an **actor question** answered by a human, recorded as a separate field (§9). The
moat is measuring coordination reproducibly and cheaply on a platform nobody else
covers; the accusation is never ours to make.

---

## 6. Architecture direction — two lenses + presets

**Structural lens** *(exists today, being re-parameterised)* — *who is acting together?*
The `CoordinationAnalyzer` (`backend/purisa/services/coordination.py`) builds a NetworkX
graph from five co-action signals (synchronised posting, URL sharing, text similarity,
hashtag overlap, reply patterns) → community detection → 0–100 score + MAD spike
detection. Purely structural; reads no *meaning*. The five signals are the field's
canonical set and stay. What changes (Phase 1): co-occurrences are **normalised by
popularity** and IDF-weighted, synchrony is computed on pairwise time differences across
the stream rather than inside hourly bins, fixed thresholds become **percentiles or
permutation-null p-values**, lexical TF-IDF becomes tiered **sentence-embedding**
similarity, and Louvain becomes **Leiden**. A sixth signal family is added for Bluesky:
**account-graph signals** (creation-time bursts, co-follow rings, handle-generation
patterns, PDS/DID provenance, engagement asymmetry) — the signals that caught every
documented Bluesky operation to date.

**Semantic lens** *(new)* — *what are they saying, and about whom?* A per-post enricher
(sentiment / stance / target, on Jev — see Phase 2) plus two new detectors:
- **Target-directed burst** — for pile-ons (who is being piled on, by how many distinct
  accounts, with what polarity). Surfaced as a **brigade-indicators panel** (trigger
  account, first-cohort amplification speed, share of newly created accounts, overlap
  with prior clusters, engagement asymmetry), not a verdict.
- **Narrative clustering** — for disinformation (group posts by *what is claimed*,
  distinct from *who is coordinating*). Built on the same embedding store as the
  structural text channel.

Semantic signals enter the engine as **edge definitions** (same target + stance within a
window; same narrative within a window), never as per-post evidence. The literature has
no ablation showing semantic labels sharpen organic-vs-coordinated separation; what they
demonstrably do is extend *which kinds* of campaigns the graph can see (URL and text
detectors find almost disjoint actor sets). Semantic edges raise a cluster's evidence
only alongside structural and account-graph signals.

**Preset system** *(new)* — one config bundles **sources + enrichers + detectors +
view**, so switching phenomenon = switching preset. Sketch:

```yaml
presets:
  pile_on:
    sources: [bluesky]
    enrichers: [sentiment, target_extraction]
    detectors:
      target_burst: { window_min: 60, min_accounts: 25, polarity: negative }
      coordination: { sync_window_s: 60, edge_threshold: p95 }   # structural coordination
      account_graph: { creation_burst: true, engagement_asymmetry: true }
    view: brigade_indicators
  disinfo_campaign:
    enrichers: [stance, narrative_embedding]
    detectors:
      narrative_cluster: { min_size: 5 }
      coordination: { url_sharing: true, text_sim: { copy: 0.8, paraphrase: 0.85 } }
    view: narrative_map
  political_sentiment:
    enrichers: [sentiment, entity_extraction]
    detectors:
      sentiment_timeline: { entities: [candidate_a, candidate_b] }
      coordination: { enabled: true }               # flag manufactured shifts
    view: sentiment_over_time
```

Thresholds shown are illustrative; real values are set per platform by the Phase 0
sweeps and live in `presets.yaml`, not in code. CIB and pump-&-dump are just presets
with the semantic enrichers off.

---

## 7. Validation methodology

The credibility section. Coordination has almost no natural ground truth, so we
manufacture trustworthy validation, in increasing order of confidence:

1. **Known-label backtests (recall).** Done for the lighthouse: the public
   **Clemson / FiveThirtyEight IRA troll-tweet dataset** — recall 97–100% at K≥3
   (`validation/RESULTS.md`). Recall on a corpus that is coordinated by construction is
   the *cheap* half; every method in the literature reaches it.
2. **Matched-control benchmark (precision + FPR).** The load-bearing leg. The X/Twitter
   IO archive is no longer available; its replacement is **OSoMe's 26-campaign Zenodo
   release** (DOI 10.5281/zenodo.14141549), which ships an `is_control` class of
   hashtag- and date-matched organic accounts. Report precision / recall / FPR per
   campaign. Realistic bar from the literature: precision ≥ 0.9 at low recall, or fused
   AUC ≈ 0.8. Second external calibration target: the court-record **South Korean NIS
   2012** list, on which CooRTweet publishes 91% (co-retweet) / 17% (co-tweet) at a 60 s
   window. Licences for both must be verified before anything but aggregate metrics is
   redistributed.
3. **Organic negative controls on Bluesky (FPR).** Build from the firehose: a
   breaking-news hour, a sports final, a protest hashtag. The four known false-positive
   archetypes are event reactions, hub accounts others sync *around*, media/ad networks,
   and generic duplicate text. No published work reports an FPR for any of these; a
   number here is ahead of the literature.
4. **Synthetic injection (ROC).** On the Guo, Hu & Zhang 2026 template: inject *N*
   synthetic accounts posting within *W* seconds into a real Bluesky hour, pair each
   with an activity-matched clean twin, sweep thresholds, report ROC with CIs over ≥3
   seeds. Calibrates `sync_window_seconds`, edge percentiles, `min_cluster_density`.
5. **Human adjudication (precision).** Sample flagged clusters; **2 raters, ≥200
   items, κ/α reported**; plus a date-level review of the ten most-misclassified windows
   against the news. Also the gate for the Jev enricher (Phase 2a).

**Headline metrics we commit to:** recall on known-label sets, **precision and
false-positive rate on matched controls and organic Bluesky bursts**, and separation
(distance between organic and coordinated distributions on the axis). Those numbers
*are* the trustworthiness. Nothing structural ships to the dashboard as a default until
leg 2 has run.

*Access caveat (confirmed 2026-09-22):* the X/Twitter state-actor archive is gone (HTTP
402; "no longer available to the public"). The IRA dataset and the OSoMe release remain
public. Bluesky, Hacker News and Mastodon need no vetting; X, Reddit, Meta and TikTok
research access all require institutional or not-for-profit affiliation.

---

## 8. Roadmap

Each phase is its own feature branch + PR (per `CLAUDE.md` git workflow). Code insertion
points below were confirmed by exploration of the current codebase. **Ordering rule
(2026-09-22):** structural fixes and the matched-control leg land before the semantic
layer; the embedding store moves from Phase 3 to Phase 1 because the engine needs it
first; Bluesky account-graph signals precede narrative clustering.

### Phase 0 — Validation harness *first*

- [x] IRA loader + recall harness (`validation/load_ira.py`, `run_validation.py`).
- [x] Run + calibrate on dense windows — `validation/RESULTS.md`. Finding: the sync
      channel saturates at any realistic density (median `sync_rate` = 1.0).
- [ ] **OSoMe matched-control benchmark.** Generalise the loader to the Zenodo files,
      tag `source_query = "validation:osome:<campaign>"`, add precision / recall / FPR
      per campaign using `is_control`. Replace the recall table in `RESULTS.md` with a
      precision/recall/FPR table.
- [ ] **Bluesky organic burst corpora** (leg 3) from the firehose; FPR per corpus.
- [ ] **Synthetic injection** (`validation/inject.py`, leg 4).
- [ ] **NIS calibration target** + written adjudication protocol in `validation/README.md`.
- [ ] `REPORT.md` with the headline metrics.

### Phase 1 — Structural re-parameterisation + preset system

Engine changes, each measured against the Phase 0 benchmark before merge:
- **De-saturate sync** (`_build_network`, `_find_synchronized_pairs`): pairwise Δt across
  the stream (not inside hourly bins); weight each co-occurrence by 1/(n−1) co-actors
  or an e^(−βΔt) kernel; IDF-weight shared URLs and hashtags; sweep the window at
  10 s / 30 s / 60 s / 90 s / 5 min and fit a per-platform inter-post-gap mixture model
  to place the cut-off empirically.
- **Statistical thresholds**: per-window percentile edge thresholds tuned on the
  benchmark, or a permutation null (shuffle object assignments, ≥1,000 iterations,
  Benjamini–Hochberg FDR) so every edge carries a p-value; eigenvector-centrality node
  pruning before the density guard.
- **Text channel** (`similarity.py`): tiered sentence-embedding similarity with a
  multilingual sentence-transformer — lexical ≥ 0.8 → "copy", embedding ≥ 0.85–0.9 →
  "paraphrase", ≥ 0.7 → "same narrative" — on per-user-pair averages within windows,
  with a generic-text filter. This creates the **embedding store** (un-parked).
- **Clustering**: Louvain → **Leiden** (keep `seed=42`) so the density guard rejects
  sparse communities, not badly connected ones; evaluate multiplex (per-layer)
  community detection instead of union-flattening once layers are normalised.
- **Score**: keep the 0–100 composite for the dashboard, but store per cluster the
  **count of independently significant signal layers (0–6)**; run `get_spikes` MAD over
  flagged-account and community *counts* per window, not over the composite.
- **Presets**: make `CoordinationConfig` loadable from `presets.yaml`, mirroring the
  `platforms.yaml` loader pattern in `collector.py`. A preset declares `sources`,
  `enrichers`, `detectors` (+thresholds), `view`. All thresholds above live here.

### Phase 2 — Semantic enrichment layer (tiered)

Decision 2026-09-22: the per-post classification tier is built on **Jev** (TypeSafe AI's
System One model: typed Choice / Score / Noul decisions with calibrated probabilities,
no text generation) instead of Claude Haiku 4.5. Rationale, cost model and risks are in
`docs/spikes/2026-09-22-jev.md`. Jev is adopted for **this one use case only**; it
does not touch the structural engine, scoring, timing, or Detoxify. The literature
supports the *shape* (small typed models for bulk classification; no generation channel
for in-post prompt injection to exploit — LLM judges lose up to 48% accuracy to it) but
offers no evidence that per-post semantic labels sharpen organic-vs-coordinated
separation, so this layer is scoped as *coverage*, not *accuracy*.

- **Phase 2a — Jev probe (gate).** Before any integration: `validation/jev_probe.py`
  over ~500 IRA originals (stratified by `account_category`) + ~500 live Bluesky
  posts, a 200-post two-rater label set (κ/α reported), an adversarial slice
  (injection-style text in posts), and an **implicit-stance / sarcasm slice** (where
  pile-on content lives and where zero-shot stance collapses). Majority-vote over ≥3
  question phrasings; compare against Haiku **and a second model family** on the same
  200; require a per-label calibration curve and an abstain band. Adopt only if
  agreement ≥ the LLM baselines, calibration is monotone, and the adversarial slice does
  not flip verdicts. Results go in `validation/JEV_RESULTS.md`, which must note that
  the vendor's 67.8% accuracy figure is self-reported and unreproduced. Requires
  `TYPESAFE_API_KEY` in `backend/.env`.
- **Phase 2b — Enricher.** New `backend/purisa/services/enricher.py` `SemanticEnricher`
  interface + `JevEnricher` implementation, following the existing inflammatory-flag +
  lazy-`@property` template in `collector.py`. Haiku or a local model must remain a
  drop-in behind the same interface (vendor-lock guardrail).
- **Tier 1:** VADER sentiment on every post. **Tier 2:** one Jev call per post asking
  every semantic question at once (sentiment, target, hostility-to-target, factual
  claim, promotional, language). Cheap enough (~$18 per million posts at ~430 input
  tokens) to run on everything collected, but throughput is capped by the 1,200
  req/min rate limit, so bulk re-enrichment is a background job, not inline.
- **Design constraint:** Jev cannot extract and produces no embeddings. Code proposes
  the candidate set (mentions, hashtags, NER, or a narrative list seeded from the
  Phase 1 embedding store); Jev picks and scores. This is the "retrieve then judge"
  pattern and it is what Phase 3 consumes.
- **Per-post labels are never evidence.** Only window-level (target, stance) and
  narrative aggregates reach the engine, as edges (§6).
- **Reproducibility (§9):** pin `model="jev-1.13.0"`; store `response.model`, full
  `probabilities` and `confidence` alongside the answer; keep question text in a
  versioned `jev_questions.py`; re-run the probe on every version bump. Never place
  instructions in `state` (posts are attacker-controlled and Jev treats state as
  non-hostile).
- Storage: start in `PostDB.platform_metadata['jev']` (JSON, **no migration**);
  promote hot fields (`sentiment_score`, `target_entity`) to real columns only if
  query performance demands.
- Hook point: inside `UniversalCollector.store_posts()` (or its call sites) before
  merge, behind a settings flag.
- Deferred, pending probe results: a Jev **cluster-triage judge** that ranks flagged
  clusters for human adjudication (§7 step 5). The best measured result for an LLM
  asked "is this cluster coordinated?" is F1 0.57; if built, its output is stored
  beside the structural score, never inside it.

### Phase 3 — New detectors

In this order:
- **Bluesky account-graph signals**: a new edge/feature family from
  `platforms/bluesky.py` + `_build_network()` — creation-time bursts, co-follow rings,
  handle-generation patterns, PDS/DID provenance, engagement asymmetry (reply-ring
  clusters with near-zero organic uptake). These caught Doppelgänger, Matryoshka and
  the multi-PDS swarms; the five co-action signals would not have.
- **Target-directed burst** (pile-ons): a new method called from
  `CoordinationAnalyzer._build_network()`, emitting generic `SimilarityResult`s with
  `similarity_type = "target_directed_burst"` from (target, stance) pairs within a
  window; clustering / scoring / storage reuse the existing path. New `edge_type` /
  `cluster_type` values; detail in `cluster_metadata`. Note that insider escalation
  without newcomer influx is a documented pile-on shape.
- **Narrative clustering** (disinfo): a post-clustering analyzer grouping posts by
  semantic narrative over the Phase 1 embedding store (embed → UMAP → HDBSCAN → label
  candidates for Jev to assign), stored as `cluster_type = "narrative"`.

### Phase 4 — Preset-aware dashboard

- Extend cluster pattern types in `frontend/src/types/coordination.ts`; add per-preset
  views (`brigade_indicators`, `narrative_map`, `sentiment_over_time`) swapped via the
  existing `useCoordination` hook and component structure in `App.tsx`.
- Every surfaced cluster carries a **confidence tier** (high / moderate / low, with
  reasons), a human-set **actor-type** field (media, activist/fandom, commercial,
  unknown), and a "no attribution" default. Emit incident-style alerts (timestamp,
  evidence, confidence, DISARM-tagged) beside the timeline — that is how practitioner
  networks operate.
- Every finding shows which platform it came from; Hacker News output is labelled
  **"unvalidated"** until a ground truth exists (none does today).

### Platforms

- **Bluesky — primary.** The only major platform with a free, complete, unauthenticated
  firehose (Jetstream ≈ 25 GB/month posts-only); 3,619 suspected-IO accounts removed
  in 2025 (self-reported); Doppelgänger and Matryoshka independently documented;
  civil society has asked for exactly this tool. Respect community norms stricter
  than the API: pseudonymise DIDs/handles in any export.
- **Hacker News — secondary, unvalidated.** Free MIT-licensed API; plausibly under-served
  for comment brigading; but no ground truth, no literature, no vote data. Must not
  consume Phase 0–1 effort.
- **Mastodon — next.** Open API, no vetting, captures bridged Threads/Bluesky content;
  respect per-instance research policies.
- **X — only with a partner.** DSA Article 40(12) requires not-for-profit or
  research-institution affiliation; a fiscal sponsor or academic partner would open X,
  Reddit, Meta Content Library and TikTok at once. Strategic choice, not a Phase 0
  blocker.

### Parked — infrastructure (the "how", decided after the "what")

Turso (edge SQLite) for the Postgres-ready DB; enricher result caching (Jev has no batch
API — one state per request — so caching by post id is the only lever). The embedding
store is **no longer parked** (Phase 1). Revisit the rest when a build target is chosen.

---

## 9. Non-goals & guardrails

- **Not a data broker.** We do not sell detections or user data. The product is insight
  and accountability, not surveillance-for-hire.
- **Precision-first.** A false "this is a brigade" is worse than a missed one — it
  manufactures a false accusation. Tune for defensibility.
- **Reproducibility.** Seeded clustering (`seed=42`), documented thresholds, and
  published validation metrics. Anyone should be able to reproduce a finding.
- **Coordination ≠ guilt.** The tool measures *structure*, not *intent*. Surface the
  evidence; let humans draw conclusions.
- **Coordination ≠ inauthenticity.** The axis is "structural coordination", never
  "engineered". Actor type is a separate, human-set field. Co-sharing alone never
  attributes anything; attribution confidence is stated as high / moderate / low with
  reasons, per practitioner standards (Nimmo; DFRLab FIAT).
- **No account-level publication without review.** Two-rater adjudication recorded
  before any account or cluster leaves the tool; DIDs and handles pseudonymised in
  exports (pseudonymised data is still personal data under GDPR).
- **Publish the method, not the verdict.** Parameters, code and evidence ship with every
  finding so it is replicable analysis, not asserted fact — the defence that has held
  in platform litigation against researchers.

---

## Appendix — current engine reference

| Concern | Location |
|---|---|
| Structural detection, clustering, scoring | `backend/purisa/services/coordination.py` (`CoordinationAnalyzer`, `CoordinationConfig`, `_build_network`, `get_spikes`) |
| Validation harness + results | `validation/` (`load_ira.py`, `run_validation.py`, `RESULTS.md`) |
| Research basis for the 2026-09-22 revisions | `docs/research/2026-09-22-cib-state-of-the-art.md`, `docs/spikes/2026-09-22-jev.md` |
| Generic detector output | `backend/purisa/services/similarity.py` (`SimilarityResult`, `TextSimilarityCalculator`) |
| Collection + enricher hook | `backend/purisa/services/collector.py` (`UniversalCollector.store_posts`) |
| New-source contract | `backend/purisa/platforms/base.py` (`SocialPlatform` ABC) |
| Enrichment storage slots | `PostDB.platform_metadata`, `cluster_metadata`, `metric_metadata` (JSON) |
| Config-loader precedent | `backend/purisa/config/platforms.yaml` |
| View layer | `frontend/src/hooks/useCoordination.ts`, `src/App.tsx`, `src/types/coordination.ts` |
