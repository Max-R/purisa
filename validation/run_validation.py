#!/usr/bin/env python3
"""
Run the unchanged CoordinationAnalyzer over a window of IRA validation data
and compute account-level recall, cluster shape/purity, and separation.

Recall = |eligible ∩ clustered| / |eligible|, where eligible = accounts with
>= K analyzer-visible posts in the window, and clustered = accounts placed in
any detected cluster. Every account in the IRA dataset is a labelled troll,
so on IRA alone this is a pure recall measurement (see validation/README.md
for what this does and does not prove).

Because "in any cluster" is a generous hit criterion, the report also shows
the cluster size distribution (one giant cluster would make recall trivial)
and, when control accounts exist, label purity and separation:

- An account is "control" when AccountDB.platform_metadata['is_control'] is
  truthy, otherwise "coordinated".
- Purity of a cluster = coordinated members / members.
- participation = windows_clustered / windows_active per account, where
  windows_active = hourly windows in the analysed range in which the account
  has >= 1 analyzer-visible post (post_type='post'), and windows_clustered =
  those windows in which it appears in a detected cluster.
- Separation = ROC-AUC of participation, coordinated (positive) vs control
  (negative), with the KS statistic as a secondary number.
  K note: separation only counts accounts with windows_active >= K, reported
  for K=3 (headline; an account seen in one or two windows has a participation
  of 0, 0.5 or 1 and says little) and K=1 (everything). This K counts active
  *windows*, unlike the recall K, which counts *posts*.

With no control accounts (the IRA-only case) purity and separation are null.

The analyzer runs exactly as in production — same config defaults, same code
path — against the isolated validation database. --sweep instead varies one
threshold at a time around the defaults (optionally over several Louvain
seeds); it rewrites the stored clusters for the analysed windows, so run it
against a disposable copy of the validation database.
"""
import hashlib
import json
import statistics
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

import click
from scipy.stats import ks_2samp
from sklearn.metrics import roc_auc_score

# Add backend to path (same pattern as cli.py)
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

from purisa.database.connection import init_database  # noqa: E402
from purisa.database.models import AccountDB, PostDB  # noqa: E402
from purisa.services.coordination import CoordinationAnalyzer, CoordinationConfig  # noqa: E402

DEFAULT_DB = REPO_ROOT / 'validation' / 'ira.db'
RECALL_K_VALUES = (1, 3, 5)  # min posts in window for an account to count as "eligible"
SEPARATION_K_VALUES = (3, 1)  # min active windows for an account to enter the separation AUC
PURITY_THRESHOLD = 0.9

# One parameter at a time around the defaults (not the full product)
SWEEP_GRID = {
    'sync_window_seconds': [10, 30, 60, 90, 300],
    'text_similarity_threshold': [0.7, 0.8, 0.9],
    'min_cluster_density': [0.2, 0.3, 0.5],
}


@dataclass
class GroundTruth:
    """Config-independent facts about the window, loaded once per invocation."""
    post_counts: dict            # account_id -> analyzer-visible posts in window
    active_windows: dict         # account_id -> set of hour starts with >= 1 post
    category_by_account: dict    # account_id -> account_category
    control_accounts: set        # account_ids with platform_metadata.is_control


def _auto_window(results_dir: Path, platform_tag: str) -> tuple[datetime, datetime]:
    """Pick the densest single day from the loader's density profile."""
    profile_path = results_dir / f'density_profile_{platform_tag}.json'
    if not profile_path.exists():
        raise click.ClickException(
            f'{profile_path} not found — run load_ira.py first, or pass --start/--end'
        )
    profile = json.loads(profile_path.read_text())
    days = Counter()
    for hour, count in profile['posts_per_hour'].items():
        days[hour[:10]] += count
    if not days:
        raise click.ClickException('Density profile is empty — did the load succeed?')
    densest_day, count = days.most_common(1)[0]
    click.echo(f'Auto-window: densest day is {densest_day} ({count:,} posts)')
    start = datetime.fromisoformat(densest_day)
    return start, start + timedelta(days=1)


def _config_hash(config: CoordinationConfig) -> str:
    """Short stable fingerprint of the analyzer config, so output names never collide."""
    payload = json.dumps(vars(config), sort_keys=True)
    return hashlib.sha1(payload.encode()).hexdigest()[:8]


def _load_ground_truth(db, platform_tag: str, start: datetime, end: datetime) -> GroundTruth:
    post_counts = Counter()
    active_windows = defaultdict(set)
    with db.get_session() as session:
        rows = (
            session.query(PostDB.account_id, PostDB.created_at)
            .filter(
                PostDB.platform == platform_tag,
                PostDB.created_at >= start,
                PostDB.created_at < end,
                PostDB.post_type == 'post',
            )
            .all()
        )
        for account_id, created_at in rows:
            post_counts[account_id] += 1
            active_windows[account_id].add(created_at.replace(minute=0, second=0, microsecond=0))

        category_by_account = {}
        control_accounts = set()
        for acct in session.query(AccountDB).filter(AccountDB.platform == platform_tag).all():
            meta = acct.platform_metadata or {}
            category_by_account[acct.id] = meta.get('account_category', 'Unknown')
            if meta.get('is_control'):
                control_accounts.add(acct.id)

    return GroundTruth(dict(post_counts), dict(active_windows), category_by_account, control_accounts)


def _size_stats(sizes: list[int], clustered_accounts: int) -> dict:
    if not sizes:
        return {'count': 0, 'min': None, 'median': None, 'mean': None, 'max': None,
                'largest_cluster_share': None}
    return {
        'count': len(sizes),
        'min': min(sizes),
        'median': statistics.median(sizes),
        'mean': round(statistics.mean(sizes), 2),
        'max': max(sizes),
        # Share of distinct clustered accounts that sit in the run's single largest cluster
        'largest_cluster_share': round(max(sizes) / clustered_accounts, 4),
    }


def _separation(truth: GroundTruth, clustered_windows: dict, analysed_windows: set) -> dict | None:
    if not truth.control_accounts:
        return None
    by_k = {}
    for k in SEPARATION_K_VALUES:
        labels, scores = [], []
        for account_id, windows in truth.active_windows.items():
            active = windows & analysed_windows
            if len(active) < k:
                continue
            hit = clustered_windows.get(account_id, set()) & active
            labels.append(0 if account_id in truth.control_accounts else 1)
            scores.append(len(hit) / len(active))
        pos = [s for s, y in zip(scores, labels) if y == 1]
        neg = [s for s, y in zip(scores, labels) if y == 0]
        both = bool(pos) and bool(neg)
        by_k[k] = {
            'n_coordinated': len(pos),
            'n_control': len(neg),
            'roc_auc': round(float(roc_auc_score(labels, scores)), 4) if both else None,
            'ks_statistic': round(float(ks_2samp(pos, neg).statistic), 4) if both else None,
        }
    return by_k


def _evaluate(results, truth: GroundTruth) -> dict:
    """Everything that depends on the analyzer output, for one run."""
    clusters = [c for r in results for c in r.clusters]
    clustered = set()
    clustered_windows = defaultdict(set)
    for result in results:
        for cluster in result.clusters:
            clustered.update(cluster.members)
            for member in cluster.members:
                clustered_windows[member].add(result.time_window_start)
    analysed_windows = {r.time_window_start for r in results}

    recall_by_k = {}
    for k in RECALL_K_VALUES:
        eligible = {a for a, n in truth.post_counts.items() if n >= k}
        hits = eligible & clustered
        recall_by_k[k] = {
            'eligible': len(eligible),
            'clustered': len(hits),
            'recall': round(len(hits) / len(eligible), 4) if eligible else None,
        }

    by_category = defaultdict(lambda: {'eligible': 0, 'clustered': 0})
    k_default = 3
    for account_id, n in truth.post_counts.items():
        if n < k_default:
            continue
        cat = truth.category_by_account.get(account_id, 'Unknown')
        by_category[cat]['eligible'] += 1
        if account_id in clustered:
            by_category[cat]['clustered'] += 1
    for cat, row in by_category.items():
        row['recall'] = round(row['clustered'] / row['eligible'], 4) if row['eligible'] else None

    if truth.control_accounts:
        purities = [
            sum(m not in truth.control_accounts for m in c.members) / len(c.members)
            for c in clusters
        ]
        purity = {
            'mean_purity': round(statistics.mean(purities), 4) if purities else None,
            'share_clusters_purity_ge_0_9': (
                round(sum(p >= PURITY_THRESHOLD for p in purities) / len(purities), 4)
                if purities else None
            ),
            'control_accounts_clustered': len(clustered & truth.control_accounts),
            'control_accounts_total': len(truth.control_accounts),
        }
    else:
        purity = {'mean_purity': None, 'share_clusters_purity_ge_0_9': None,
                  'control_accounts_clustered': None, 'control_accounts_total': 0}

    # Controls carry no troll category; counting them would make an all-control
    # cluster (or a troll cluster padded with controls) look single-category
    single_category = sum(
        len({truth.category_by_account.get(m, 'Unknown')
             for m in c.members if m not in truth.control_accounts}) == 1
        for c in clusters
    )
    category_coclustering = {
        'single_category_clusters': single_category,
        'share_single_category': round(single_category / len(clusters), 4) if clusters else None,
    }

    hourly = [{
        'hour': r.time_window_start.isoformat(),
        'posts': r.total_posts,
        'coordinated_posts': r.coordinated_posts,
        'clusters': len(r.clusters),
        'coordination_score': round(r.coordination_score, 2),
        'sync_rate': round(r.sync_rate, 4),
        'text_similarity_rate': round(r.text_similarity_rate, 4),
    } for r in results]

    return {
        'recall_by_min_posts': recall_by_k,
        'recall_by_category_k3': dict(by_category),
        'cluster_sizes': _size_stats([len(c.members) for c in clusters], len(clustered)),
        'purity': purity,
        'category_coclustering': category_coclustering,
        'separation_by_min_windows': _separation(truth, clustered_windows, analysed_windows),
        'totals': {
            'active_accounts': len(truth.post_counts),
            'clustered_accounts': len(clustered),
            'control_accounts': len(truth.control_accounts),
            'posts_analyzed': sum(r.total_posts for r in results),
            'clusters_detected': len(clusters),
        },
        'hourly': hourly,
    }


def _fmt_pct(value) -> str:
    return f'{value:.1%}' if value is not None else 'n/a'


def _print_report(metrics: dict, platform_tag: str, start: datetime, end: datetime):
    click.echo(f'\n=== Recall ({platform_tag}, {start} → {end}) ===')
    for k, row in metrics['recall_by_min_posts'].items():
        click.echo(f'  K>={k}:  {row["clustered"]:>5}/{row["eligible"]:<5} eligible accounts clustered'
                   f'  →  recall {_fmt_pct(row["recall"])}')
    click.echo('\n=== Per category (K>=3) ===')
    for cat, row in sorted(metrics['recall_by_category_k3'].items()):
        click.echo(f'  {cat:<15} {row["clustered"]:>5}/{row["eligible"]:<5}  {_fmt_pct(row["recall"])}')

    sizes = metrics['cluster_sizes']
    click.echo('\n=== Cluster sizes ===')
    if sizes['count']:
        click.echo(f'  {sizes["count"]} clusters · min {sizes["min"]} · median {sizes["median"]} · '
                   f'mean {sizes["mean"]} · max {sizes["max"]}')
        click.echo(f'  largest cluster holds {_fmt_pct(sizes["largest_cluster_share"])} of clustered accounts')
    else:
        click.echo('  no clusters detected')
    cc = metrics['category_coclustering']
    click.echo(f'  single-category clusters: {cc["single_category_clusters"]}/{sizes["count"]}'
               f'  ({_fmt_pct(cc["share_single_category"])})')

    purity = metrics['purity']
    click.echo('\n=== Purity ===')
    if purity['mean_purity'] is None and not purity['control_accounts_total']:
        click.echo('  purity: n/a (no control accounts)')
    else:
        click.echo(f'  mean purity {_fmt_pct(purity["mean_purity"])} · '
                   f'clusters with purity >= {PURITY_THRESHOLD}: '
                   f'{_fmt_pct(purity["share_clusters_purity_ge_0_9"])}')
        click.echo(f'  control accounts clustered (false positives): '
                   f'{purity["control_accounts_clustered"]}/{purity["control_accounts_total"]}')

    click.echo('\n=== Separation (participation ROC-AUC, coordinated vs control) ===')
    separation = metrics['separation_by_min_windows']
    if separation is None:
        click.echo('  separation: n/a (no control accounts)')
    else:
        for k, row in separation.items():
            auc = f'{row["roc_auc"]:.3f}' if row['roc_auc'] is not None else 'n/a'
            ks = f'{row["ks_statistic"]:.3f}' if row['ks_statistic'] is not None else 'n/a'
            click.echo(f'  windows_active>={k}:  AUC {auc}  KS {ks}  '
                       f'(n={row["n_coordinated"]} coordinated / {row["n_control"]} control)')


def _run(platform_tag: str, start: datetime, end: datetime, config: CoordinationConfig,
         truth: GroundTruth) -> tuple[dict, float]:
    analyzer = CoordinationAnalyzer(config)
    t0 = time.monotonic()
    results = analyzer.analyze_range(platform_tag, start, end)
    return _evaluate(results, truth), time.monotonic() - t0


def _sweep_configs(seeds: list[int]):
    """Yield (param, value, seed, config): one parameter varied at a time around the defaults."""
    for param, values in SWEEP_GRID.items():
        for value in values:
            for seed in seeds:
                yield param, value, seed, CoordinationConfig(**{param: value, 'louvain_seed': seed})


def _parse_seeds(raw: str) -> list[int]:
    try:
        return [int(s) for s in raw.split(',') if s.strip()]
    except ValueError:
        raise click.BadParameter(f'expected comma-separated integers, got {raw!r}', param_hint='--seeds')


@click.command()
@click.option('--db', 'db_path', type=click.Path(path_type=Path), default=DEFAULT_DB,
              help='Validation SQLite database')
@click.option('--platform-tag', default='ira', help='Platform value used at load time')
@click.option('--start', type=click.DateTime(formats=['%Y-%m-%d', '%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']),
              default=None, help='Window start (ISO, e.g. 2016-10-01T00:00)')
@click.option('--end', type=click.DateTime(formats=['%Y-%m-%d', '%Y-%m-%dT%H:%M', '%Y-%m-%dT%H:%M:%S']),
              default=None, help='Window end (ISO, exclusive)')
@click.option('--auto-window', is_flag=True, help='Analyze the densest day from the density profile')
@click.option('--output', type=click.Path(path_type=Path), default=None,
              help='Output JSON path (default: validation/results/metrics_<tag>_<start>_<end>_<confighash>.json, '
                   'or sweep_<tag>_<start>_<end>.json with --sweep)')
@click.option('--sweep', is_flag=True,
              help='Vary sync window, text threshold and cluster density one at a time around the '
                   'defaults. Rewrites stored clusters — use a disposable DB copy.')
@click.option('--seeds', default='42', show_default=True,
              help='Comma-separated Louvain seeds; a single run takes exactly one, --sweep repeats each config per seed')
@click.option('--allow-rewrite', is_flag=True,
              help='Permit --sweep on a DB whose filename contains neither "sweep" nor "copy"')
def main(db_path: Path, platform_tag: str, start: datetime, end: datetime,
         auto_window: bool, output: Path, sweep: bool, seeds: str, allow_rewrite: bool):
    """Analyze a window of validation data and report recall, cluster shape, purity and separation."""
    seed_list = _parse_seeds(seeds)
    if not seed_list:
        raise click.BadParameter('at least one seed required', param_hint='--seeds')
    if not sweep and len(seed_list) > 1:
        raise click.BadParameter('multiple seeds only make sense with --sweep', param_hint='--seeds')
    if sweep and not allow_rewrite and not any(w in db_path.name.lower() for w in ('sweep', 'copy')):
        raise click.ClickException(
            f'--sweep rewrites the stored clusters in {db_path.name}; run it on a copy whose filename '
            f'contains "sweep" or "copy", or pass --allow-rewrite'
        )

    results_dir = db_path.parent / 'results'
    if auto_window:
        start, end = _auto_window(results_dir, platform_tag)
    if not start or not end:
        raise click.ClickException('Pass --start and --end, or --auto-window')
    if not db_path.exists():
        raise click.ClickException(f'{db_path} not found — run load_ira.py first')

    db = init_database(f'sqlite:///{db_path}')
    truth = _load_ground_truth(db, platform_tag, start, end)
    results_dir.mkdir(exist_ok=True)
    window_tag = f'{start.strftime("%Y%m%dT%H%M")}_{end.strftime("%Y%m%dT%H%M")}'
    n_windows = int((end - start).total_seconds() // 3600)

    if sweep:
        _main_sweep(db_path, platform_tag, start, end, truth, seed_list, n_windows,
                    output or results_dir / f'sweep_{platform_tag}_{window_tag}.json')
        return

    config = CoordinationConfig(louvain_seed=seed_list[0])
    config_hash = _config_hash(config)
    click.echo(f'Analyzing {platform_tag} from {start} to {end} ({n_windows} hourly windows)')
    evaluation, elapsed = _run(platform_tag, start, end, config, truth)

    metrics = {
        'generated_for': {
            'platform_tag': platform_tag,
            'db': str(db_path),
            'window': {'start': start.isoformat(), 'end': end.isoformat()},
            'analyzer_config': vars(config),
            'config_hash': config_hash,
            'runtime_seconds': round(elapsed, 1),
        },
        **evaluation,
    }
    if output is None:
        output = results_dir / f'metrics_{platform_tag}_{window_tag}_{config_hash}.json'
    output.write_text(json.dumps(metrics, indent=2))

    _print_report(metrics, platform_tag, start, end)
    click.echo(f'\nAnalysis took {elapsed:.0f}s. Metrics written to {output}')


def _main_sweep(db_path: Path, platform_tag: str, start: datetime, end: datetime,
                truth: GroundTruth, seeds: list[int], n_windows: int, output: Path):
    runs = list(_sweep_configs(seeds))
    click.echo(f'Sweeping {platform_tag} from {start} to {end} ({n_windows} hourly windows): '
               f'{len(runs)} runs ({len(runs) // len(seeds)} configs × {len(seeds)} seeds)')

    # The default config recurs once per swept parameter; analyse it once per seed
    cache = {}
    rows = []
    for i, (param, value, seed, config) in enumerate(runs, 1):
        config_hash = _config_hash(config)
        reused = config_hash in cache
        if not reused:
            click.echo(f'  [{i}/{len(runs)}] {param}={value} seed={seed} ...', nl=False)
            cache[config_hash] = _run(platform_tag, start, end, config, truth)
            click.echo(f' {cache[config_hash][1]:.0f}s')
        evaluation, elapsed = cache[config_hash]
        rows.append({
            'swept_param': param,
            'swept_value': value,
            'seed': seed,
            'config_hash': config_hash,
            'analyzer_config': vars(config),
            'reused_identical_config': reused,
            'runtime_seconds': round(elapsed, 1),
            'recall_by_min_posts': evaluation['recall_by_min_posts'],
            'clusters_detected': evaluation['totals']['clusters_detected'],
            'clustered_accounts': evaluation['totals']['clustered_accounts'],
            'cluster_sizes': evaluation['cluster_sizes'],
            'purity': evaluation['purity'],
            'separation_by_min_windows': evaluation['separation_by_min_windows'],
        })

    sweep = {
        'generated_for': {
            'platform_tag': platform_tag,
            'db': str(db_path),
            'window': {'start': start.isoformat(), 'end': end.isoformat()},
            'grid': SWEEP_GRID,
            'seeds': seeds,
            'baseline_config': vars(CoordinationConfig()),
        },
        'rows': rows,
    }
    output.write_text(json.dumps(sweep, indent=2))

    click.echo(f'\n=== Sweep ({platform_tag}, {start} → {end}) ===')
    click.echo(f'  {"param":<26} {"value":>6} {"seed":>5} {"clusters":>8} {"K>=1":>7} {"K>=3":>7} {"K>=5":>7} '
               f'{"med sz":>6} {"max sz":>6} {"largest":>7} {"AUC k3":>7}')
    for row in rows:
        recall = row['recall_by_min_posts']
        sizes = row['cluster_sizes']
        sep = row['separation_by_min_windows']
        auc = sep[3]['roc_auc'] if sep and sep[3]['roc_auc'] is not None else None
        click.echo(
            f'  {row["swept_param"]:<26} {row["swept_value"]:>6} {row["seed"]:>5} {row["clusters_detected"]:>8} '
            f'{_fmt_pct(recall[1]["recall"]):>7} {_fmt_pct(recall[3]["recall"]):>7} {_fmt_pct(recall[5]["recall"]):>7} '
            f'{sizes["median"] if sizes["median"] is not None else "n/a":>6} '
            f'{sizes["max"] if sizes["max"] is not None else "n/a":>6} '
            f'{_fmt_pct(sizes["largest_cluster_share"]):>7} '
            f'{f"{auc:.3f}" if auc is not None else "n/a":>7}'
        )
    if all(row['separation_by_min_windows'] is None for row in rows):
        click.echo('  separation: n/a (no control accounts)')
    click.echo(f'\nSweep written to {output}')


if __name__ == '__main__':
    main()
