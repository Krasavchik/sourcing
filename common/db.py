# common/db.py
import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------------------------------------------------------
# 1. Fetch Supabase Postgres URL (set as secret or .env variable)
# ------------------------------------------------------------------
SUPABASE_DB_URL = os.getenv("SUPABASE_DB_URL")
if not SUPABASE_DB_URL:
    logger.error("SUPABASE_DB_URL env var not found.")
    raise RuntimeError(
        "SUPABASE_DB_URL env var not found ‒ supply the Supabase Postgres "
        "connection string, e.g. "
    )
else:
    logger.info("Loaded SUPABASE_DB_URL from environment.")

# ------------------------------------------------------------------
# 2. Ensure sslmode=require (Supabase mandates SSL)
#    - if the string already has `?sslmode=` keep it
# ------------------------------------------------------------------
if "sslmode=" not in SUPABASE_DB_URL:
    SUPABASE_DB_URL += "?sslmode=require"
    logger.info("Appended sslmode=require to DB URL.")
else:
    logger.info("DB URL already contains sslmode.")

logger.info("Creating SQLAlchemy engine.")
engine = create_engine(
    SUPABASE_DB_URL,
    future=True,
    echo=False,               # flip to True for SQL debug
    pool_pre_ping=True,
)

SessionFactory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

Base = declarative_base()

@contextmanager
def get_session():
    """Context-manager wrapper around a short-lived DB session."""
    logger.info("Opening new database session.")
    try:
        with SessionFactory() as session:
            yield session
            logger.info("Session committed successfully.")
    except Exception as e:
        logger.error(f"Session error: {e}", exc_info=True)
        raise
    finally:
        logger.info("Session closed.")
