#!/usr/bin/env python3
"""
Run the unchanged CoordinationAnalyzer over a window of IRA validation data
and compute account-level recall.

Recall = |eligible ∩ clustered| / |eligible|, where eligible = accounts with
>= K analyzer-visible posts in the window, and clustered = accounts placed in
any detected cluster. Every account in the IRA dataset is a labelled troll,
so this is a pure recall measurement (see validation/README.md for what this
does and does not prove).

The analyzer runs exactly as in production — same config defaults, same code
path — against the isolated validation database.
"""
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import click
from sqlalchemy import func

# Add backend to path (same pattern as cli.py)
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

from purisa.database.connection import init_database  # noqa: E402
from purisa.database.models import AccountDB, PostDB  # noqa: E402
from purisa.services.coordination import CoordinationAnalyzer  # noqa: E402

DEFAULT_DB = REPO_ROOT / 'validation' / 'ira.db'
RECALL_K_VALUES = (1, 3, 5)  # min posts in window for an account to count as "eligible"


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
              help='Metrics JSON path (default: validation/results/metrics_<tag>_<start>.json)')
def main(db_path: Path, platform_tag: str, start: datetime, end: datetime,
         auto_window: bool, output: Path):
    """Analyze a window of validation data and report recall."""
    results_dir = db_path.parent / 'results'
    if auto_window:
        start, end = _auto_window(results_dir, platform_tag)
    if not start or not end:
        raise click.ClickException('Pass --start and --end, or --auto-window')
    if not db_path.exists():
        raise click.ClickException(f'{db_path} not found — run load_ira.py first')

    db = init_database(f'sqlite:///{db_path}')

    click.echo(f'Analyzing {platform_tag} from {start} to {end} '
               f'({int((end - start).total_seconds() // 3600)} hourly windows)')
    analyzer = CoordinationAnalyzer()
    results = analyzer.analyze_range(platform_tag, start, end)

    # --- Recall ---------------------------------------------------------
    with db.get_session() as session:
        post_counts = dict(
            session.query(PostDB.account_id, func.count(PostDB.id))
            .filter(
                PostDB.platform == platform_tag,
                PostDB.created_at >= start,
                PostDB.created_at < end,
                PostDB.post_type == 'post',
            )
            .group_by(PostDB.account_id)
            .all()
        )
        category_by_account = {
            acct.id: (acct.platform_metadata or {}).get('account_category', 'Unknown')
            for acct in session.query(AccountDB).filter(AccountDB.platform == platform_tag).all()
        }

    clustered = set()
    for result in results:
        for cluster in result.clusters:
            clustered.update(cluster.members)

    recall_by_k = {}
    for k in RECALL_K_VALUES:
        eligible = {a for a, n in post_counts.items() if n >= k}
        hits = eligible & clustered
        recall_by_k[k] = {
            'eligible': len(eligible),
            'clustered': len(hits),
            'recall': round(len(hits) / len(eligible), 4) if eligible else None,
        }

    by_category = defaultdict(lambda: {'eligible': 0, 'clustered': 0})
    k_default = 3
    for account_id, n in post_counts.items():
        if n < k_default:
            continue
        cat = category_by_account.get(account_id, 'Unknown')
        by_category[cat]['eligible'] += 1
        if account_id in clustered:
            by_category[cat]['clustered'] += 1
    for cat, row in by_category.items():
        row['recall'] = round(row['clustered'] / row['eligible'], 4) if row['eligible'] else None

    hourly = [{
        'hour': r.time_window_start.isoformat(),
        'posts': r.total_posts,
        'coordinated_posts': r.coordinated_posts,
        'clusters': len(r.clusters),
        'coordination_score': round(r.coordination_score, 2),
        'sync_rate': round(r.sync_rate, 4),
        'text_similarity_rate': round(r.text_similarity_rate, 4),
    } for r in results]

    metrics = {
        'generated_for': {
            'platform_tag': platform_tag,
            'db': str(db_path),
            'window': {'start': start.isoformat(), 'end': end.isoformat()},
            'analyzer_config': vars(analyzer.config),
        },
        'recall_by_min_posts': recall_by_k,
        'recall_by_category_k3': dict(by_category),
        'totals': {
            'active_accounts': len(post_counts),
            'clustered_accounts': len(clustered),
            'posts_analyzed': sum(r.total_posts for r in results),
            'clusters_detected': sum(len(r.clusters) for r in results),
        },
        'hourly': hourly,
    }

    results_dir.mkdir(exist_ok=True)
    if output is None:
        output = results_dir / f'metrics_{platform_tag}_{start.strftime("%Y%m%dT%H%M")}.json'
    output.write_text(json.dumps(metrics, indent=2))

    # --- Report ---------------------------------------------------------
    click.echo(f'\n=== Recall ({platform_tag}, {start} → {end}) ===')
    for k, row in recall_by_k.items():
        recall = f"{row['recall']:.1%}" if row['recall'] is not None else 'n/a'
        click.echo(f'  K>={k}:  {row["clustered"]:>5}/{row["eligible"]:<5} eligible accounts clustered  →  recall {recall}')
    click.echo(f'\n=== Per category (K>={k_default}) ===')
    for cat, row in sorted(by_category.items()):
        recall = f"{row['recall']:.1%}" if row['recall'] is not None else 'n/a'
        click.echo(f'  {cat:<15} {row["clustered"]:>5}/{row["eligible"]:<5}  {recall}')
    click.echo(f'\nMetrics written to {output}')


if __name__ == '__main__':
    main()
