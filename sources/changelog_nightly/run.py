import typer, os
import logging
from datetime import datetime, timedelta
from common.db import get_session
from common.models import RawItem, ItemType
from .parser import parse_page
from sqlalchemy.exc import IntegrityError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = typer.Typer()

@app.command()
def main(date: str = None, dry_run: bool = False):
    """Scrape Changelog Nightly for <date> (YYYY/MM/DD). Defaults to yesterday UTC."""
    try:
        day = datetime.utcnow().date() - timedelta(days=1) if not date else datetime.fromisoformat(date).date()
        logger.info(f"Selected date: {day}")
        url = f"https://nightly.changelog.com/{day:%Y/%m/%d}"
        logger.info(f"Fetching and parsing URL: {url}")
        rows = parse_page(url)
        logger.info(f"Parsed {len(rows)} rows from {url}")
        if dry_run:
            typer.echo(f"Would insert {len(rows)} rows")
            logger.info(f"Dry run: would insert {len(rows)} rows")
            return
        with get_session() as s:
            for r in rows:
                obj = RawItem(**{**r, "item_type": ItemType[r["item_type"]]})
                try:
                    s.add(obj)
                    s.commit()
                except IntegrityError:
                    s.rollback()  # Ignore duplicates
        typer.echo(f"Inserted {len(rows)} rows from {url}")
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    app()