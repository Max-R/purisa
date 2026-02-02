"""Database connection and session management."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging
from .models import Base
# Import coordination models to register them with Base
from . import coordination_models  # noqa: F401

logger = logging.getLogger(__name__)


class Database:
    """Database connection manager."""

    def __init__(self, database_url: str):
        """
        Initialize database connection.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url

        # Special handling for SQLite
        if database_url.startswith('sqlite'):
            self.engine = create_engine(
                database_url,
                connect_args={'check_same_thread': False},
                poolclass=StaticPool
            )
        else:
            self.engine = create_engine(database_url)

        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        logger.info(f"Database initialized: {database_url}")

    def create_tables(self):
        """Create all database tables."""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    def drop_tables(self):
        """Drop all database tables (use with caution!)."""
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("Database tables dropped")

    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session with context manager.

        Yields:
            SQLAlchemy session

        Example:
            with db.get_session() as session:
                session.query(AccountDB).all()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_session_direct(self) -> Session:
        """
        Get a database session (caller must close).

        Returns:
            SQLAlchemy session
        """
        return self.SessionLocal()


# Global database instance (initialized in main.py or config)
_db_instance: Database = None


def init_database(database_url: str) -> Database:
    """
    Initialize global database instance.

    Args:
        database_url: SQLAlchemy database URL

    Returns:
        Database instance
    """
    global _db_instance
    _db_instance = Database(database_url)
    _db_instance.create_tables()
    return _db_instance


def get_database() -> Database:
    """
    Get global database instance.

    Returns:
        Database instance

    Raises:
        RuntimeError: If database not initialized
    """
    if _db_instance is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    return _db_instance
