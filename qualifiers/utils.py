from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import text
from common.models import Entity

def upsert_entity(s, name, e_type, url, meta):
    stmt = (
        insert(Entity)
        .values(name=name, entity_type=e_type, canonical_url=url, meta=meta)
        .on_conflict_do_update(
            index_elements=[Entity.canonical_url],
            set_=dict(name=name, meta=meta)
        )
        .returning(Entity.id)
    )
    return s.execute(stmt).scalar_one()

def link_raw_to_entities(raw_id, entity_ids, session):
    """Link a raw item to multiple entities."""
    for entity_id in entity_ids:
        session.execute(text(
            "INSERT INTO item_entity_map (raw_id, entity_id) VALUES (:raw_id, :entity_id) "
            "ON CONFLICT DO NOTHING"
        ), {"raw_id": raw_id, "entity_id": entity_id})