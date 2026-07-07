# Purisa — Vision

*The strategy of record. Living document. Last updated 2026-06-24.*

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
2. **Product hypothesis** — *Researchers and journalists will trust and act on an
   organic-vs-engineered score they didn't compute themselves.* (Does anyone care?)

**Analytical correctness leads.** For a civic tool, a wrong answer doesn't just lose a
sale — it manufactures a false accusation. Credibility is the product. We test the
engine before we sell the story.

---

## 5. The differentiator

The organic ↔ coordinated axis — the thing pure sentiment tools cannot measure, because
they lack a graph layer:

- Many people **independently** angry → high volume, **low** inter-account coordination.
- A coordinated **brigade** → high volume, **high** coordination (synchronised timing,
  shared copypasta/links, clustered account ages).

Purisa plots a pile-on on that axis. The same trick separates grassroots political
sentiment from astroturfed sentiment. This is the moat.

---

## 6. Architecture direction — two lenses + presets

**Structural lens** *(exists today)* — *who is acting together?* The
`CoordinationAnalyzer` (`backend/purisa/services/coordination.py`) builds a NetworkX
graph from five signals (synchronised posting, URL sharing, TF-IDF text similarity,
hashtag overlap, reply patterns) → Louvain clusters → 0–100 score + MAD spike detection.
Purely structural; reads no *meaning*.

**Semantic lens** *(new)* — *what are they saying, and about whom?* A per-post enricher
(sentiment / stance / target) plus two new detectors:
- **Target-directed burst** — for pile-ons (who is being piled on, by how many distinct
  accounts, with what polarity).
- **Narrative clustering** — for disinformation (group posts by *what is claimed*,
  distinct from *who is coordinating*).

**Preset system** *(new)* — one config bundles **sources + enrichers + detectors +
view**, so switching phenomenon = switching preset. Sketch:

```yaml
presets:
  pile_on:
    sources: [bluesky]
    enrichers: [sentiment, target_extraction]
    detectors:
      target_burst: { window_min: 60, min_accounts: 25, polarity: negative }
      coordination: { sync_window_s: 90 }          # measures organic-vs-brigade
    view: target_leaderboard
  disinfo_campaign:
    enrichers: [stance, narrative_embedding]
    detectors:
      narrative_cluster: { min_size: 5 }
      coordination: { url_sharing: true, text_sim: 0.8 }
    view: narrative_map
  political_sentiment:
    enrichers: [sentiment, entity_extraction]
    detectors:
      sentiment_timeline: { entities: [candidate_a, candidate_b] }
      coordination: { enabled: true }               # flag manufactured shifts
    view: sentiment_over_time
```

CIB and pump-&-dump are just presets with the semantic enrichers off.

---

## 7. Validation methodology

The credibility section. Coordination has almost no natural ground truth, so we
manufacture trustworthy validation, in increasing order of confidence:

1. **Known-label backtests (recall).** Run the engine on datasets where the coordinated
   set is already known. Lighthouse: the public **Clemson / FiveThirtyEight IRA
   troll-tweet dataset** (~3M tweets) — does Purisa cluster it? Also classic labelled
   bot/sockpuppet corpora (e.g. cresci-2017) and documented pump-&-dump schemes (SEC
   litigation releases, published Telegram-pump datasets).
2. **Synthetic injection (precision + sensitivity).** Inject *N* synthetic coordinated
   accounts (known sync timing, copypasta) into a real organic stream; sweep thresholds;
   plot an **ROC** to calibrate `sync_window_seconds`, `text_similarity_threshold`,
   `min_cluster_density`.
3. **Negative controls (false-positive rate).** Run on benign-but-busy communities (a
   sports fandom mid-game = high volume, high text similarity, **zero** coordination
   intent). If Purisa flags them, the signals over-fire. This protects the mission.
4. **Organic-vs-coordinated separation (the differentiator).** Replay documented events
   with expert/journalistic consensus on brigade-vs-grassroots; check the engine places
   them on the right side of the axis.
5. **Human adjudication (precision).** Sample flagged clusters; ≥2 raters label them;
   report inter-rater agreement + precision.

**Headline metrics we commit to:** recall on known-label sets, false-positive rate on
negative controls, and **separation** (distance between organic and coordinated
distributions on the axis). Those three numbers *are* the trustworthiness.

*Access caveat:* the X/Twitter state-actor transparency archive is harder to obtain
post-2023; confirm availability before relying on it. The IRA dataset remains public.

---

## 8. Roadmap

Each phase is its own feature branch + PR (per `CLAUDE.md` git workflow). Code insertion
points below were confirmed by exploration of the current codebase.

### Phase 0 — Validation harness *first* (lighthouse: CIB recall on IRA dataset)

The first build is *validation*, not features — prove the existing engine works before
expanding it.
- Ingest the IRA dataset as a read-only source: either a lightweight `SocialPlatform`
  adapter (subclass the ABC in `backend/purisa/platforms/base.py`, transform rows →
  `Post`) or a direct CSV → `PostDB` loader tagged `source_query = "validation:ira"`.
- Run the **unchanged** `CoordinationAnalyzer.analyze_range()`.
- Measure recall (labelled coordinated set), false-positive rate (benign control), and a
  synthetic-injection ROC to calibrate thresholds.
- Output: a `validation/` report + script. This is the analytical-hypothesis test.

### Phase 1 — Preset system (config-driven detection)

- Make `CoordinationConfig` (currently hardcoded dataclass defaults, **not** loaded from
  config) loadable from a new `presets.yaml`, mirroring the `platforms.yaml` loader
  pattern in `collector.py`.
- A preset declares `sources`, `enrichers`, `detectors` (+thresholds), `view`.

### Phase 2 — Semantic enrichment layer (tiered)

- New `backend/purisa/services/enricher.py` `SemanticEnricher`, following the existing
  inflammatory-flag + lazy-`@property` template in `collector.py`.
- **Tier 1:** VADER sentiment on every post. **Tier 2:** Claude Haiku 4.5 for
  stance / target / narrative on posts the structural detectors already flag
  (cost-bounded — never the full firehose).
- Storage: start in `PostDB.platform_metadata` (JSON, **no migration**); promote hot
  fields (`sentiment_score`, `target_entity`) to real columns only if query performance
  demands.
- Hook point: inside `UniversalCollector.store_posts()` (or its call sites) before merge.

### Phase 3 — New detectors

- **Target-directed burst** (pile-ons): a new method called from
  `CoordinationAnalyzer._build_network()`, emitting generic `SimilarityResult`s with
  `similarity_type = "target_directed_burst"`; clustering / scoring / storage reuse the
  existing path. New `edge_type` / `cluster_type` values; detail in `cluster_metadata`.
- **Narrative clustering** (disinfo): a post-Louvain analyzer grouping posts by semantic
  narrative (embeddings), stored as `cluster_type = "narrative"`.

### Phase 4 — Preset-aware dashboard

- Extend cluster pattern types in `frontend/src/types/coordination.ts`; add per-preset
  views (`target_leaderboard`, `narrative_map`, `sentiment_over_time`) swapped via the
  existing `useCoordination` hook and component structure in `App.tsx`.

### Parked — infrastructure (the "how", decided after the "what")

Turso (edge SQLite) for the Postgres-ready DB; an embedding store for narrative
clustering; LLM-enricher batching/caching. Revisit when a build target is chosen.

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

---

## Appendix — current engine reference

| Concern | Location |
|---|---|
| Structural detection, clustering, scoring | `backend/purisa/services/coordination.py` (`CoordinationAnalyzer`, `CoordinationConfig`, `_build_network`, `get_spikes`) |
| Generic detector output | `backend/purisa/services/similarity.py` (`SimilarityResult`, `TextSimilarityCalculator`) |
| Collection + enricher hook | `backend/purisa/services/collector.py` (`UniversalCollector.store_posts`) |
| New-source contract | `backend/purisa/platforms/base.py` (`SocialPlatform` ABC) |
| Enrichment storage slots | `PostDB.platform_metadata`, `cluster_metadata`, `metric_metadata` (JSON) |
| Config-loader precedent | `backend/purisa/config/platforms.yaml` |
| View layer | `frontend/src/hooks/useCoordination.ts`, `src/App.tsx`, `src/types/coordination.ts` |
