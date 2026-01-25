#!/usr/bin/env python3
"""
Purisa CLI Tool

Command-line interface for Purisa bot detection system.
"""
import asyncio
import click
import sys
import os
from pathlib import Path
import tabulate as tabulate_module
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent / 'backend'
sys.path.insert(0, str(backend_path))

from purisa.database.connection import init_database, get_database
from purisa.database.models import AccountDB, PostDB, ScoreDB, FlagDB
from purisa.services.collector import UniversalCollector
from purisa.services.analyzer import BotDetector
from purisa.config.settings import get_settings


@click.group()
def cli():
    """Purisa - Multi-platform social media bot detection system."""
    # Initialize database
    settings = get_settings()
    init_database(settings.database_url)


@cli.command()
@click.option('--platform', type=str, help='Platform to collect from (bluesky, hackernews)')
@click.option('--query', type=str, multiple=True, help='Search query or hashtag (can be specified multiple times)')
@click.option('--limit', type=int, default=50, help='Number of posts to collect per query')
def collect(platform, query, limit):
    """Collect posts from social media platforms."""
    async def _collect():
        collector = UniversalCollector()

        if platform and query:
            # Collect from specific platform with multiple queries
            total_posts = 0
            for q in query:
                click.echo(f"Collecting {limit} posts from {platform} with query: {q}")
                posts = await collector.collect_from_platform(platform, q, limit)
                await collector.store_posts(posts)
                click.echo(f"  ✓ Collected and stored {len(posts)} posts for '{q}'")
                total_posts += len(posts)

            click.echo(f"\n✓ Total: Collected and stored {total_posts} posts from {len(query)} queries")
        else:
            # Run full collection cycle
            click.echo("Running full collection cycle for all platforms...")
            await collector.run_collection_cycle()
            click.echo("✓ Collection cycle completed")

    asyncio.run(_collect())


@cli.command()
@click.option('--account', type=str, help='Specific account ID to analyze')
@click.option('--platform', type=str, help='Analyze all accounts from platform')
def analyze(account, platform):
    """Analyze accounts for bot-like behavior."""
    analyzer = BotDetector()

    if account:
        # Analyze specific account
        click.echo(f"Analyzing account: {account}")
        score = analyzer.analyze_account(account)

        if score:
            click.echo(f"\nBot Detection Score: {score.total_score:.2f}/10.0")
            click.echo(f"Flagged: {'YES' if score.flagged else 'NO'}")
            click.echo(f"\nSignal Breakdown:")

            table_data = [[signal, f"{value:.2f}"] for signal, value in score.signals.items()]
            click.echo(tabulate_module.tabulate(table_data, headers=['Signal', 'Score'], tablefmt='simple'))
        else:
            click.echo("✗ Account not found")
    else:
        # Analyze all accounts
        click.echo(f"Analyzing all accounts{f' from {platform}' if platform else ''}...")
        scores = analyzer.analyze_all_accounts(platform=platform)

        flagged_count = sum(1 for s in scores if s.flagged)
        click.echo(f"\n✓ Analyzed {len(scores)} accounts")
        click.echo(f"  Flagged: {flagged_count}")
        click.echo(f"  Clean: {len(scores) - flagged_count}")


@cli.command()
@click.option('--platform', type=str, help='Filter by platform')
@click.option('--all', 'show_all', is_flag=True, help='Show all flagged accounts')
def flagged(platform, show_all):
    """Show flagged accounts."""
    db = get_database()

    with db.get_session() as session:
        # Get flagged scores
        query = session.query(ScoreDB).filter_by(flagged=1)
        scores = query.all()

        if not scores:
            click.echo("No flagged accounts found")
            return

        # Get account details
        results = []
        for score in scores:
            account = session.query(AccountDB).filter_by(id=score.account_id).first()
            if account:
                # Apply platform filter
                if platform and account.platform != platform:
                    continue

                results.append([
                    account.username[:30],
                    account.platform,
                    f"{score.total_score:.1f}",
                    account.post_count,
                    account.follower_count
                ])

        if results:
            click.echo(f"\nFlagged Accounts ({len(results)} total):\n")
            headers = ['Username', 'Platform', 'Score', 'Posts', 'Followers']

            if show_all:
                click.echo(tabulate_module.tabulate(results, headers=headers, tablefmt='grid'))
            else:
                # Show first 20
                click.echo(tabulate_module.tabulate(results[:20], headers=headers, tablefmt='grid'))
                if len(results) > 20:
                    click.echo(f"\n... and {len(results) - 20} more (use --all to see all)")
        else:
            click.echo("No flagged accounts found matching filters")


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
        flagged_accounts = session.query(ScoreDB).filter_by(flagged=1).count()

        # Platform breakdown
        platform_stats = []
        for plat in ['bluesky', 'hackernews']:
            acc_count = session.query(AccountDB).filter_by(platform=plat).count()
            post_count = session.query(PostDB).filter_by(platform=plat).count()
            platform_stats.append([plat, acc_count, post_count])

        # Display stats
        click.echo("\n=== Purisa Statistics ===\n")
        click.echo(f"Total Accounts: {total_accounts}")
        click.echo(f"Total Posts: {total_posts}")
        click.echo(f"Flagged Accounts: {flagged_accounts}")

        if total_accounts > 0:
            flag_rate = (flagged_accounts / total_accounts) * 100
            click.echo(f"Flag Rate: {flag_rate:.1f}%")

        click.echo("\n=== Platform Breakdown ===\n")
        click.echo(tabulate_module.tabulate(
            platform_stats,
            headers=['Platform', 'Accounts', 'Posts'],
            tablefmt='grid'
        ))


@cli.command()
def init():
    """Initialize database and verify setup."""
    click.echo("Initializing Purisa...")

    settings = get_settings()
    click.echo(f"Database URL: {settings.database_url}")

    # Initialize database
    db = init_database(settings.database_url)
    click.echo("✓ Database initialized")

    # Check platform configuration
    collector = UniversalCollector()
    platforms = collector.get_available_platforms()

    click.echo(f"\n✓ Available platforms: {', '.join(platforms)}")

    if not platforms:
        click.echo("\n⚠ Warning: No platforms configured!")
        click.echo("  Make sure to set environment variables:")
        click.echo("  - BLUESKY_HANDLE")
        click.echo("  - BLUESKY_PASSWORD")

    click.echo("\n✓ Purisa is ready to use!")
    click.echo("\nNext steps:")
    click.echo("  1. Run 'python cli.py collect' to start collecting data")
    click.echo("  2. Run 'python cli.py analyze' to detect bots")
    click.echo("  3. Run 'python cli.py flagged' to see flagged accounts")


if __name__ == '__main__':
    # Add tabulate to requirements if not already there
    try:
        import tabulate
    except ImportError:
        print("Installing tabulate for better output formatting...")
        os.system("pip install tabulate")
        import tabulate

    cli()
