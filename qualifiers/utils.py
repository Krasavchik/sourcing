from sqlalchemy.dialects.postgresql import insert
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