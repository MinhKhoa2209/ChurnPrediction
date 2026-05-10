import logging
import time
from functools import wraps
from typing import Any, Callable, TypeVar

from sqlalchemy import create_engine
from sqlalchemy.exc import DBAPIError, OperationalError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from backend.config import settings

logger = logging.getLogger(__name__)


T = TypeVar("T")


engine = create_engine(
    settings.database_url,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
    pool_pre_ping=True,
    echo=settings.debug,
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


Base = declarative_base()


def retry_on_db_error(max_retries: int = 3, base_delay: float = 1.0) -> Callable:
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except (OperationalError, DBAPIError) as e:
                    last_exception = e

                    if attempt < max_retries:
                        delay = base_delay * (2**attempt)

                        logger.warning(
                            f"Database operation failed (attempt {attempt + 1}/{max_retries + 1}): {str(e)}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )

                        time.sleep(delay)
                    else:
                        logger.error(
                            f"Database operation failed after {max_retries + 1} attempts: {str(e)}"
                        )

            raise last_exception

        return wrapper

    return decorator


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_database_health() -> bool:
    try:
        from sqlalchemy import text

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            conn.commit()
        return True
    except (OperationalError, DBAPIError) as e:
        logger.error(f"Database health check failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Database health check failed with unexpected error: {e}")
        return False
