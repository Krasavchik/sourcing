# common/models.py
from datetime import datetime, timezone
import enum

from sqlalchemy import (
    Column, Integer, String, JSON, TIMESTAMP, Enum, UniqueConstraint, ForeignKey, Numeric, ARRAY
)
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.dialects.postgresql import insert

Base = declarative_base()

# ------------------------------------------------------------------  
# 0. Shared enums
# ------------------------------------------------------------------
class ItemType(enum.Enum):
    project = "project"
    person  = "person"
    company = "company"
    unknown = "unknown"


class EntityType(enum.Enum):
    project = "project"
    person  = "person"
    company = "company"
    dataset = "dataset"
    unknown = "unknown"


# ------------------------------------------------------------------  
# 1. Raw scrape table (already existed)
# ------------------------------------------------------------------
class RawItem(Base):
    __tablename__ = "raw_items"

    id          = Column(Integer, primary_key=True)
    source      = Column(String, nullable=False)
    external_id = Column(String, nullable=False)
    item_type   = Column(Enum(ItemType))
    title       = Column(String)
    url         = Column(String)
    meta        = Column("metadata", JSON, default=dict)
    scraped_at  = Column(TIMESTAMP(timezone=True),
                         default=lambda: datetime.now(timezone.utc))

    __table_args__ = (UniqueConstraint("source", "external_id"),)


# ------------------------------------------------------------------  
# 2. Canonical entity table  ← NEW
# ------------------------------------------------------------------
class Entity(Base):
    __tablename__ = "entities"

    id            = Column(Integer, primary_key=True)
    name          = Column(String)
    entity_type   = Column(Enum(EntityType))
    canonical_url = Column(String, unique=True)
    meta          = Column(JSON, default=dict)
    created_at    = Column(TIMESTAMP(timezone=True),
                           default=lambda: datetime.now(timezone.utc))

    # convenience: back-ref list of raw links
    raw_links = relationship("ItemEntityMap", back_populates="entity")

# ── add just below the Entity class ─────────────────────────────────
class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    src_id     = Column(Integer,
                        ForeignKey("entities.id", ondelete="CASCADE"),
                        primary_key=True)
    dst_id     = Column(Integer,
                        ForeignKey("entities.id", ondelete="CASCADE"),
                        primary_key=True)
    rel_type   = Column(String, primary_key=True)      # composite PK
    confidence = Column(Numeric, default=1.0, nullable=False)

    # optional back-refs if you ever need them
    src = relationship("Entity", foreign_keys=[src_id])
    dst = relationship("Entity", foreign_keys=[dst_id])


# ------------------------------------------------------------------  
# 3. Link table raw ↔ entity  ← NEW
# ------------------------------------------------------------------
class ItemEntityMap(Base):
    __tablename__ = "item_entity_map"

    raw_id     = Column(Integer, ForeignKey("raw_items.id", ondelete="CASCADE"), primary_key=True)
    entity_id  = Column(Integer, ForeignKey("entities.id",  ondelete="CASCADE"), primary_key=True)
    confidence = Column(Numeric)

    raw_item   = relationship("RawItem")
    entity     = relationship("Entity", back_populates="raw_links")

class Opportunity(Base):
    """
    One row per investable cluster (project-only, owner+project, etc.)
    """
    __tablename__ = "opportunities"

    id               = Column(Integer, primary_key=True)
    anchor_entity_id = Column(Integer,
                              ForeignKey("entities.id", ondelete="CASCADE"),
                              unique=True, nullable=False)
    anchor_type      = Column(String,  nullable=False)          # 'project' | 'person' | 'company'

    # Postgres int[] → SQLAlchemy ARRAY(Integer)
    related_project_ids  = Column(ARRAY(Integer), default=list, nullable=False)
    related_person_ids   = Column(ARRAY(Integer), default=list, nullable=False)
    related_company_ids  = Column(ARRAY(Integer), default=list, nullable=False)

    meta        = Column(JSON, default=dict)
    score       = Column(Numeric)
    updated_at  = Column(TIMESTAMP(timezone=True),
                         default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))

    # optional helper: back-reference to anchor entity
    anchor = relationship("Entity")