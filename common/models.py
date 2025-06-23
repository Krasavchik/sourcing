# common/models.py
from datetime import datetime, timezone
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    TIMESTAMP,
    Enum,
    UniqueConstraint,
)

from .db import Base


# ---------------------------------------------------------------------------
# 1.  Python-side enumeration (business values)
# ---------------------------------------------------------------------------
class ItemType(enum.Enum):
    project = "project"
    person  = "person"
    company = "company"
    dataset = "dataset"
    unknown = "unknown"


# ---------------------------------------------------------------------------
# 2.  Raw scrape table (immutable history)
# ---------------------------------------------------------------------------
class RawItem(Base):
    __tablename__ = "raw_items"

    id          = Column(Integer, primary_key=True)
    source      = Column(String, nullable=False)
    external_id = Column(String, nullable=False)

    # ——— Enum column: point to the **existing** DB type enum_item
    item_type = Column(
        Enum(
            ItemType,          # the Python enum
            name="enum_item",  # MUST match the Postgres enum you created
            native_enum=True,  # cast as ::enum_item in SQL
            create_type=False  # don't try to CREATE TYPE again
        )
    )

    title = Column(String)
    url   = Column(String)

    # expose as .meta in Python, keep "metadata" in Postgres
    meta  = Column("metadata", JSON, default=dict)

    scraped_at = Column(
        TIMESTAMP(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )

    # (source, external_id) must be unique so re-scraping is idempotent
    __table_args__ = (
        UniqueConstraint("source", "external_id", name="uq_raw_items_source_external_id"),
    )

    # optional: nice debug representation
    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"<RawItem id={self.id} source={self.source} "
            f"external_id={self.external_id} url={self.url}>"
        )