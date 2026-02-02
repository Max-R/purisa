#!/usr/bin/env python3
"""
Purisa CLI Tool (2.0)

Command-line interface for Purisa coordination detection system.
Detects coordinated inauthentic behavior patterns in social media.
"""
import asyncio
import click
import sys
import os
from pathlib import Path
import tabulate as tabulate_module
from datetime import datetime, timedelta

# Add backend to path and load environment
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

# Load environment variables from backend/.env
from dotenv import load_dotenv
env_file = backend_path / '.env'
if env_file.exists():
    load_dotenv(env_file)

from purisa.database.connection import init_database, get_database
from purisa.database.models import AccountDB, PostDB
from purisa.database.coordination_models import CoordinationMetricDB, CoordinationClusterDB
from purisa.services.collector import UniversalCollector
from purisa.services.coordination import CoordinationAnalyzer
from purisa.config.settings import get_settings

# Progress bar support
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False


@click.group()
def cli():
    """Purisa 2.0 - Coordination detection for social media platforms."""
    # Initialize database
    settings = get_settings()
    init_database(settings.database_url)


@cli.command()
@click.option('--platform', type=str, help='Platform to collect from (bluesky, hackernews)')
@click.option('--query', type=str, multiple=True, help='Search query or hashtag (can be specified multiple times)')
@click.option('--limit', type=int, default=50, help='Number of posts to collect per query')
@click.option('--harvest-comments/--no-harvest-comments', default=True, help='Harvest comments from top-performing posts')
def collect(platform, query, limit, harvest_comments):
    """Collect posts from social media platforms."""
    async def _collect():
        collector = UniversalCollector()

        if platform and query:
            # Collect from specific platform with multiple queries
            total_posts = 0
            all_posts = []

            # Progress bar for queries
            query_iter = tqdm(query, desc="Queries", unit="query") if TQDM_AVAILABLE else query

            for q in query_iter:
                if TQDM_AVAILABLE:
                    query_iter.set_postfix(current=q[:20])
                else:
                    click.echo(f"Collecting {limit} posts from {platform} with query: {q}")

                posts = await collector.collect_from_platform(platform, q, limit)
                await collector.store_posts(posts)
                all_posts.extend(posts)

                if not TQDM_AVAILABLE:
                    click.echo(f"  ✓ Collected and stored {len(posts)} posts for '{q}'")
                total_posts += len(posts)

            click.echo(f"\n✓ Collected and stored {total_posts} posts from {len(query)} queries")

            # Harvest comments from top performers
            if harvest_comments and all_posts:
                click.echo("\nIdentifying top-performing posts...")
                top_posts, stats = collector._identify_top_performers(all_posts, return_stats=True)

                click.echo(f"  Posts qualifying: {stats['posts_qualifying']}/{stats['posts_collected']} "
                          f"(threshold: {stats['min_engagement_score']})")

                if stats['posts_capped'] > 0:
                    click.echo(f"  Capped at: {stats['max_posts_for_comment_harvest']} "
                              f"({stats['posts_capped']} skipped)")

                if top_posts:
                    click.echo(f"\nHarvesting comments from {len(top_posts)} top posts...")

                    # Progress bar for comment harvesting
                    if TQDM_AVAILABLE:
                        pbar = tqdm(total=len(top_posts), desc="Harvesting comments", unit="post")

                    total_comments = 0
                    for i, post in enumerate(top_posts):
                        comments = await collector._harvest_comments_for_post(post)
                        total_comments += len(comments) if comments else 0

                        if TQDM_AVAILABLE:
                            pbar.update(1)
                            pbar.set_postfix(comments=total_comments)
                        elif (i + 1) % 5 == 0 or (i + 1) == len(top_posts):
                            click.echo(f"  Progress: {i + 1}/{len(top_posts)} posts, {total_comments} comments")

                    if TQDM_AVAILABLE:
                        pbar.close()

                    click.echo(f"\n✓ Harvested {total_comments} comments from {len(top_posts)} top posts")
                else:
                    click.echo("  No posts met engagement threshold for comment harvesting")
        else:
            # Run full collection cycle
            click.echo("Running full collection cycle for all platforms...")
            await collector.run_collection_cycle()
            click.echo("✓ Collection cycle completed")

    asyncio.run(_collect())


@cli.command()
@click.option('--platform', type=str, required=True, help='Platform to analyze (bluesky, hackernews)')
@click.option('--hours', type=int, default=24, help='Hours to analyze (default: 24)')
@click.option('--start', type=str, help='Start datetime (ISO format, e.g., 2024-01-15T00:00:00)')
def analyze(platform, hours, start):
    """Run coordination analysis on collected data.

    Analyzes posts for coordinated behavior patterns including:
    - Synchronized posting (posts within 90 seconds)
    - URL sharing (same links posted by different accounts)
    - Text similarity (similar content using TF-IDF)
    - Reply patterns (accounts commenting on same posts)

    Results are stored in the database and can be viewed with 'spikes' command.
    """
    analyzer = CoordinationAnalyzer()

    # Determine time range
    if start:
        try:
            start_time = datetime.fromisoformat(start)
        except ValueError:
            click.echo("Error: Invalid start datetime format. Use ISO format (e.g., 2024-01-15T00:00:00)")
            return
        end_time = start_time + timedelta(hours=hours)
    else:
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)

    click.echo(f"\n=== Coordination Analysis ===")
    click.echo(f"Platform: {platform}")
    click.echo(f"Time range: {start_time.strftime('%Y-%m-%d %H:%M')} to {end_time.strftime('%Y-%m-%d %H:%M')}")
    click.echo(f"Hours to analyze: {hours}\n")

    # Calculate total hours for progress bar
    total_hours = int((end_time - start_time).total_seconds() / 3600)

    if TQDM_AVAILABLE:
        pbar = tqdm(total=total_hours, desc="Analyzing", unit="hour")

    current = start_time.replace(minute=0, second=0, microsecond=0)
    results = []
    total_clusters = 0
    total_coordinated = 0
    max_score = 0.0

    db = get_database()
    with db.get_session() as session:
        while current < end_time:
            result = analyzer.analyze_hour(platform, current, session)
            results.append(result)

            total_clusters += len(result.clusters)
            total_coordinated += result.coordinated_posts
            max_score = max(max_score, result.coordination_score)

            if TQDM_AVAILABLE:
                pbar.update(1)
                pbar.set_postfix(
                    score=f"{result.coordination_score:.1f}",
                    clusters=len(result.clusters)
                )
            else:
                if result.coordination_score > 0:
                    click.echo(f"  {current.strftime('%Y-%m-%d %H:%M')}: "
                              f"score={result.coordination_score:.1f}, "
                              f"clusters={len(result.clusters)}, "
                              f"posts={result.total_posts}")

            current += timedelta(hours=1)

    if TQDM_AVAILABLE:
        pbar.close()

    # Summary
    total_posts = sum(r.total_posts for r in results)
    avg_score = sum(r.coordination_score for r in results) / len(results) if results else 0

    click.echo(f"\n=== Analysis Summary ===")
    click.echo(f"Hours analyzed: {len(results)}")
    click.echo(f"Total posts: {total_posts}")
    click.echo(f"Coordinated posts: {total_coordinated}")
    click.echo(f"Clusters detected: {total_clusters}")
    click.echo(f"Average coordination score: {avg_score:.1f}/100")
    click.echo(f"Peak coordination score: {max_score:.1f}/100")

    # Show hours with high coordination
    high_coord = [r for r in results if r.coordination_score >= 20]
    if high_coord:
        click.echo(f"\n=== High Coordination Hours ({len(high_coord)}) ===")
        for r in sorted(high_coord, key=lambda x: x.coordination_score, reverse=True)[:5]:
            click.echo(f"  {r.time_window_start.strftime('%Y-%m-%d %H:%M')}: "
                      f"score={r.coordination_score:.1f}, clusters={len(r.clusters)}")


@cli.command()
@click.option('--platform', type=str, required=True, help='Platform to check (bluesky, hackernews)')
@click.option('--hours', type=int, default=168, help='Hours to look back (default: 168 = 7 days)')
@click.option('--threshold', type=float, default=2.0, help='Standard deviations above mean (default: 2.0)')
def spikes(platform, hours, threshold):
    """Show coordination spikes above baseline.

    Identifies hours where coordination activity is significantly above
    the normal baseline (measured in standard deviations).
    """
    analyzer = CoordinationAnalyzer()

    click.echo(f"\n=== Coordination Spikes ===")
    click.echo(f"Platform: {platform}")
    click.echo(f"Looking back: {hours} hours ({hours // 24} days)")
    click.echo(f"Threshold: {threshold} standard deviations\n")

    spike_list = analyzer.get_spikes(platform, hours, threshold)

    if not spike_list:
        click.echo("No coordination spikes detected in this time range.")
        click.echo("\nTip: Try running 'purisa analyze' first to generate coordination metrics.")
        return

    # Display spikes
    table_data = []
    for spike in spike_list[:20]:
        table_data.append([
            spike['time_bucket'][:16],  # Truncate to datetime
            f"{spike['coordination_score']:.1f}",
            f"{spike['z_score']:.2f}σ",
            spike['cluster_count'],
            spike['total_posts'],
        ])

    headers = ['Time', 'Score', 'Magnitude', 'Clusters', 'Posts']
    click.echo(tabulate_module.tabulate(table_data, headers=headers, tablefmt='grid'))

    if len(spike_list) > 20:
        click.echo(f"\n... and {len(spike_list) - 20} more spikes")

    # Show baseline info
    if spike_list:
        click.echo(f"\nBaseline: mean={spike_list[0]['baseline_mean']:.1f}, "
                  f"std={spike_list[0]['baseline_std']:.1f}")


@cli.command()
@click.option('--platform', type=str, help='Filter by platform')
def stats(platform):
    """Show statistics and overview."""
    db = get_database()

    with db.get_session() as session:
        # Get counts
        accounts_query = session.query(AccountDB)
        posts_query = session.query(PostDB)

        if platform:
            accounts_query = accounts_query.filter_by(platform=platform)
            posts_query = posts_query.filter_by(platform=platform)

        total_accounts = accounts_query.count()
        total_posts = posts_query.count()

        # Platform breakdown
        platform_stats = []
        for plat in ['bluesky', 'hackernews']:
            acc_count = session.query(AccountDB).filter_by(platform=plat).count()
            post_count = session.query(PostDB).filter_by(platform=plat).count()
            platform_stats.append([plat, acc_count, post_count])

        # Coordination metrics (last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        recent_metrics = session.query(CoordinationMetricDB).filter(
            CoordinationMetricDB.time_bucket >= cutoff
        ).all()

        total_clusters = session.query(CoordinationClusterDB).count()
        recent_clusters = sum(m.active_cluster_count for m in recent_metrics)

        # Display stats
        click.echo("\n=== Purisa 2.0 Statistics ===\n")
        click.echo(f"Total Accounts: {total_accounts}")
        click.echo(f"Total Posts: {total_posts}")
        click.echo(f"Total Clusters Detected: {total_clusters}")

        click.echo("\n=== Platform Breakdown ===\n")
        click.echo(tabulate_module.tabulate(
            platform_stats,
            headers=['Platform', 'Accounts', 'Posts'],
            tablefmt='grid'
        ))

        # Coordination summary (last 24h)
        if recent_metrics:
            avg_score = sum(m.coordination_score for m in recent_metrics) / len(recent_metrics)
            max_score = max(m.coordination_score for m in recent_metrics)
            total_coordinated = sum(m.coordinated_posts_count for m in recent_metrics)

            click.echo("\n=== Coordination (Last 24 Hours) ===\n")
            click.echo(f"Hours analyzed: {len(recent_metrics)}")
            click.echo(f"Average coordination score: {avg_score:.1f}/100")
            click.echo(f"Peak coordination score: {max_score:.1f}/100")
            click.echo(f"Coordinated posts detected: {total_coordinated}")
            click.echo(f"Active clusters: {recent_clusters}")
        else:
            click.echo("\n=== Coordination ===\n")
            click.echo("No coordination analysis run yet.")
            click.echo("Run 'purisa analyze --platform <platform>' to start.")


@cli.command()
def init():
    """Initialize database and verify setup."""
    click.echo("Initializing Purisa 2.0...")

    settings = get_settings()
    click.echo(f"Database URL: {settings.database_url}")

    # Initialize database
    db = init_database(settings.database_url)
    click.echo("✓ Database initialized (including coordination tables)")

    # Check platform configuration
    collector = UniversalCollector()
    platforms = collector.get_available_platforms()

    click.echo(f"\n✓ Available platforms: {', '.join(platforms)}")

    if not platforms:
        click.echo("\n⚠ Warning: No platforms configured!")
        click.echo("  Make sure to set environment variables:")
        click.echo("  - BLUESKY_HANDLE")
        click.echo("  - BLUESKY_PASSWORD")

    click.echo("\n✓ Purisa 2.0 is ready to use!")
    click.echo("\nWorkflow:")
    click.echo("  1. Run 'purisa collect --platform bluesky --query \"#topic\"' to collect posts")
    click.echo("  2. Run 'purisa analyze --platform bluesky' to detect coordination")
    click.echo("  3. Run 'purisa spikes --platform bluesky' to see coordination spikes")
    click.echo("  4. Run 'purisa stats' to see overall statistics")


if __name__ == '__main__':
    # Add tabulate to requirements if not already there
    try:
        import tabulate
    except ImportError:
        print("Installing tabulate for better output formatting...")
        os.system("pip install tabulate")
        import tabulate

    cli()
