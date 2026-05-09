"""
Database Infrastructure
Provides database connection and session management
"""

import logging
import time
from functools import wraps
from typing import Callable, TypeVar, Any

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError, DBAPIError

from backend.config import settings

logger = logging.getLogger(__name__)

# Type variable for generic function return type
T = TypeVar('T')

# Create SQLAlchemy engine
engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,  # Verify connections before using them
    echo=settings.debug,  # Log SQL queries in debug mode
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base for models
Base = declarative_base()


def retry_on_db_error(max_retries: int = 3, base_delay: float = 1.0) -> Callable:
    """
    Decorator to retry database operations with exponential backoff
    
    Requirement 20.7: Retry failed database connections 3 times with exponential backoff
    
    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Base delay in seconds for exponential backoff (default: 1.0)
    
    Returns:
        Decorated function with retry logic
    
    Raises:
        OperationalError: After exhausting all retries
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for initial attempt
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DBAPIError) as e:
                    last_exception = e
                    
                    if attempt < max_retries:
                        # Calculate exponential backoff delay: base_delay * (2 ^ attempt)
                        delay = base_delay * (2 ** attempt)
                        
                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        
                        time.sleep(delay)
                    else:
                        # Exhausted all retries
                        logger.error(
                            f"Database operation failed after {max_retries + 1} attempts: {str(e)}"
                        )
            
            # Raise the last exception after exhausting retries
            raise last_exception  # type: ignore
        
        return wrapper
    return decorator


def get_db():
    """
    Dependency function to get database session
    Yields a database session and ensures it's closed after use
    
    - 30.2: Return 503 Service Unavailable when database is down
    
    Raises:
        OperationalError: If database connection fails
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """
    Simple dependency function to get database session without retry
    Use this for FastAPI Depends to avoid generator issues
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> bool:
    """
    Check if database is available and healthy
    
    
    Returns:
        True if database is healthy, False otherwise
    """
    try:
        # Use text() for raw SQL execution
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        return True
    except (OperationalError, DBAPIError) as e:
        logger.error(f"Database health check failed: {e}")
        return False
    except Exception as e:
        # Catch any other exceptions (like async driver issues)
        logger.error(f"Database health check failed with unexpected error: {e}")
        return False
