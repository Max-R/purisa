#!/usr/bin/env python3
"""
Load the FiveThirtyEight/Clemson IRA troll-tweet dataset into a validation database.

Reads IRAhandle_tweets_*.csv from validation/data/ and writes AccountDB/PostDB
rows to validation/ira.db (never purisa.db). Every row is tagged
platform=<platform-tag> and source_query="validation:ira" so validation data
is isolated from production data at both the file and the query level.

Retweet handling (see validation/README.md):
  exclude (default) -> stored with post_type='retweet', invisible to the analyzer
  include           -> stored as post_type='post', analyzer sees them
  skip              -> not loaded

Prints a posts-per-day density profile at the end to help pick analysis windows.
"""
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import click
import pandas as pd
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

# Add backend to path (same pattern as cli.py)
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / 'backend'))

from purisa.database.connection import init_database  # noqa: E402
from purisa.database.models import AccountDB, PostDB  # noqa: E402

DEFAULT_DB = REPO_ROOT / 'validation' / 'ira.db'
DEFAULT_DATA_DIR = REPO_ROOT / 'validation' / 'data'
SOURCE_QUERY = 'validation:ira'
DATE_FORMAT = '%m/%d/%Y %H:%M'  # e.g. "10/1/2017 22:43" — timezone undocumented, assumed UTC


def _is_retweet(row) -> bool:
    return row.get('retweet') == '1' or row.get('post_type') == 'RETWEET'


def _post_id(platform_tag: str, row) -> str:
    tweet_id = row.get('tweet_id', '')
    if tweet_id:
        return f'{platform_tag}:{tweet_id}'
    # Deterministic fallback for rows without a tweet_id
    digest = hashlib.sha1(
        f"{row.get('author', '')}|{row.get('publish_date', '')}|{row.get('content', '')}".encode()
    ).hexdigest()[:16]
    return f'{platform_tag}:h:{digest}'


def _safe_int(value, default=0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


@click.command()
@click.option('--data-dir', type=click.Path(path_type=Path), default=DEFAULT_DATA_DIR,
              help='Directory containing IRAhandle_tweets_*.csv')
@click.option('--db', 'db_path', type=click.Path(path_type=Path), default=DEFAULT_DB,
              help='SQLite file for the validation database')
@click.option('--platform-tag', default='ira',
              help='Platform value for loaded rows (use e.g. "ira_rt" for a with-retweets variant)')
@click.option('--retweet-mode', type=click.Choice(['exclude', 'include', 'skip']), default='exclude',
              help='exclude: load as post_type=retweet (analyzer ignores); include: load as posts; skip: drop')
@click.option('--limit-files', type=int, default=None, help='Only load the first N CSVs (smoke test)')
@click.option('--chunk-size', type=int, default=50_000, help='CSV read/insert batch size')
def main(data_dir: Path, db_path: Path, platform_tag: str, retweet_mode: str,
         limit_files: int, chunk_size: int):
    """Load IRA CSVs into the validation database."""
    csv_files = sorted(data_dir.glob('IRAhandle_tweets_*.csv'))
    if not csv_files:
        raise click.ClickException(
            f'No IRAhandle_tweets_*.csv in {data_dir} — run validation/download_ira.sh first'
        )
    if limit_files:
        csv_files = csv_files[:limit_files]

    db = init_database(f'sqlite:///{db_path}')
    engine = db.engine

    accounts = {}            # account_id -> column dict (only ~2,800 — kept in memory)
    hour_density = Counter()  # 'YYYY-MM-DD HH' -> post count (analyzer-visible posts only)
    stats = Counter()

    for csv_file in csv_files:
        click.echo(f'Loading {csv_file.name} ...')
        reader = pd.read_csv(csv_file, dtype=str, keep_default_na=False, chunksize=chunk_size)
        for chunk in reader:
            chunk['_created_at'] = pd.to_datetime(
                chunk['publish_date'], format=DATE_FORMAT, errors='coerce'
            )
            post_rows = []
            for row in chunk.to_dict('records'):
                created_at = row['_created_at']
                if pd.isna(created_at):
                    stats['bad_date'] += 1
                    continue
                created_at = created_at.to_pydatetime()

                retweet = _is_retweet(row)
                if retweet and retweet_mode == 'skip':
                    stats['retweets_skipped'] += 1
                    continue
                post_type = 'retweet' if (retweet and retweet_mode == 'exclude') else 'post'

                author = (row.get('author') or 'unknown').strip().lower()
                account_id = f'{platform_tag}:{author}'

                acct = accounts.setdefault(account_id, {
                    'id': account_id,
                    'username': author,
                    'platform': platform_tag,
                    'follower_count': 0,
                    'following_count': 0,
                    'post_count': 0,
                    'platform_metadata': {
                        'account_category': row.get('account_category', ''),
                        'account_type': row.get('account_type', ''),
                        'region': row.get('region', ''),
                        'dataset': 'fivethirtyeight-ira',
                    },
                })
                acct['follower_count'] = max(acct['follower_count'], _safe_int(row.get('followers')))
                acct['following_count'] = max(acct['following_count'], _safe_int(row.get('following')))
                acct['post_count'] = max(acct['post_count'], _safe_int(row.get('updates')))

                post_rows.append({
                    'id': _post_id(platform_tag, row),
                    'account_id': account_id,
                    'platform': platform_tag,
                    'content': row.get('content', ''),
                    'created_at': created_at,
                    'engagement': {},
                    'platform_metadata': {
                        'language': row.get('language', ''),
                        'account_category': row.get('account_category', ''),
                        'post_type_raw': row.get('post_type', ''),
                        'retweet': retweet,
                        'article_url': row.get('article_url', ''),
                    },
                    'source_query': SOURCE_QUERY,
                    'post_type': post_type,
                })
                stats['retweets_loaded' if retweet else 'originals_loaded'] += 1
                if post_type == 'post':
                    hour_density[created_at.strftime('%Y-%m-%d %H')] += 1

            if post_rows:
                with engine.begin() as conn:
                    conn.execute(
                        sqlite_insert(PostDB.__table__).on_conflict_do_nothing(index_elements=['id']),
                        post_rows,
                    )
        click.echo(f'  running totals: {dict(stats)}')

    if accounts:
        with engine.begin() as conn:
            conn.execute(
                sqlite_insert(AccountDB.__table__).on_conflict_do_nothing(index_elements=['id']),
                list(accounts.values()),
            )

    # Density profile — pick analysis windows from this instead of scanning 6 years
    day_density = Counter()
    for hour, count in hour_density.items():
        day_density[hour[:10]] += count

    # Results live next to the DB, so scratch/test runs never touch validation/results/
    results_dir = db_path.parent / 'results'
    results_dir.mkdir(exist_ok=True)
    profile_path = results_dir / f'density_profile_{platform_tag}.json'
    profile_path.write_text(json.dumps({
        'platform_tag': platform_tag,
        'retweet_mode': retweet_mode,
        'stats': dict(stats),
        'accounts': len(accounts),
        'posts_per_hour': dict(sorted(hour_density.items())),
    }, indent=2))

    click.echo(f'\nLoaded {len(accounts)} accounts | {dict(stats)}')
    click.echo(f'Density profile written to {profile_path}')
    click.echo('\nTop 20 densest days (analyzer-visible posts):')
    for day, count in day_density.most_common(20):
        click.echo(f'  {day}  {count:>8,} posts')


if __name__ == '__main__':
    main()
