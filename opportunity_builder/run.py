"""
opportunity_builder/run.py
Phase-3 job: turn deterministic owner–project edges into opportunities.
Run AFTER the qualifiers, BEFORE the scorer.
"""

# ── stdlib ───────────────────────────────────────────────
import logging
from datetime import datetime, timezone

# ── sqlalchemy ───────────────────────────────────────────
from sqlalchemy import text, func
from sqlalchemy.dialects.postgresql import insert
from common.db     import get_session
from common.models import Opportunity          # ← add this model in models.py

logger = logging.getLogger(__name__)


def build_opportunities():
    sql = text(
        """
        SELECT  p.id   AS proj_id,
                r.src_id        AS owner_id,
                o.entity_type   AS owner_type
        FROM    entities            p
        JOIN    entity_relationships r
                 ON r.dst_id   = p.id
                AND r.rel_type = 'owns'
        JOIN    entities            o
                 ON o.id = r.src_id
        LEFT    JOIN opportunities  opp
                 ON opp.anchor_entity_id = p.id
        WHERE   p.entity_type = 'project'
          AND   opp.id IS NULL
        """
    )

    with get_session() as s:
        rows = list(s.execute(sql))
        logger.info("Found %d new project–owner pairs", len(rows))

        for proj_id, owner_id, owner_type in rows:
            company_ids = [owner_id] if owner_type == "company" else []
            person_ids  = [owner_id] if owner_type == "person"  else []

            stmt = insert(Opportunity).values(
                anchor_entity_id    = proj_id,
                anchor_type         = "project",
                related_project_ids = [proj_id],
                related_company_ids = company_ids,
                related_person_ids  = person_ids,
                meta                = {"source": "CHANGELOG_NIGHTLY"},
                updated_at          = datetime.now(timezone.utc),
            )
            stmt = stmt.on_conflict_do_nothing(index_elements=['anchor_entity_id'])
            s.execute(stmt)

        s.commit()
        logger.info("Inserted %d opportunity rows", len(rows))


if __name__ == "__main__":
    build_opportunities()