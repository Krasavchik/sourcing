"""
qualifiers/github_repo_enrich/run.py
Enriches GitHub repos (projects) and their owners (person / company).
Activated when the raw_item URL starts with https://github.com/
"""

# ── stdlib ────────────────────────────────────────────────
from functools import lru_cache

# ── project helpers ───────────────────────────────────────
from qualifiers.utils      import upsert_entity
import logging
from qualifiers.registry   import qualifier                # decorator
from common.github         import repo as gh_repo
from common.github         import owner as gh_owner
from qualifiers.utils      import link_raw_to_entities     # tiny helper

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------
# Caching GitHub calls for the duration of the batch
# ---------------------------------------------------------------------
@lru_cache(maxsize=20_000)
def _repo(owner: str, name: str) -> dict:
    return gh_repo(owner, name)


@lru_cache(maxsize=20_000)
def _owner(login: str) -> dict:
    return gh_owner(login)


# ---------------------------------------------------------------------
# Qualifier plug-in
# ---------------------------------------------------------------------
@qualifier(lambda raw: raw.url.startswith("https://github.com/"))
def enrich(raw, session):
    """
    • Upsert a project entity for the repo
    • Upsert a person/company entity for the owner
    • Create item-entity links
    """
    try:
        owner, repo_name = raw.external_id.split("/", 1)
    except ValueError:
        logger.warning("Malformed external_id: %s", raw.external_id)
        return

    repo_json   = _repo(owner, repo_name)
    owner_json  = _owner(owner)

    # ── build rich meta dicts ─────────────────────────────
    project_meta = {
        "description"   : repo_json["description"],
        "topics"        : repo_json.get("topics", []),
        "homepage"      : repo_json["homepage"],
        "license"       : (repo_json["license"] or {}).get("spdx_id"),
        "language"      : repo_json["language"],
        "stars"         : repo_json["stargazers_count"],
        "forks"         : repo_json["forks_count"],
        "watchers"      : repo_json["subscribers_count"],
        "open_issues"   : repo_json["open_issues_count"],
        "created_at"    : repo_json["created_at"],
        "pushed_at"     : repo_json["pushed_at"],
    }

    owner_meta = {
        "name"          : owner_json["name"],
        "followers"     : owner_json["followers"],
        "bio"           : owner_json["bio"],
        "blog"          : owner_json["blog"],
        "location"      : owner_json["location"],
        "company"       : owner_json["company"],
        "public_repos"  : owner_json["public_repos"],
        "twitter"       : owner_json.get("twitter_username"),
    }

    # ── upsert entities ───────────────────────────────────
    proj_id = upsert_entity(
        session,
        name         = repo_json["name"],
        e_type       = "project",
        url          = raw.url,
        meta         = project_meta,
    )

    owner_type = "person" if owner_json["type"] == "User" else "company"
    owner_id = upsert_entity(
        session,
        name         = owner_json["login"],
        e_type       = owner_type,
        url          = owner_json["html_url"],
        meta         = owner_meta,
    )

    # ── link raw → entities ───────────────────────────────
    link_raw_to_entities(raw.id, [proj_id, owner_id], session)

    logger.info(
        "Upserted %-35s stars=%-6d owner=%s followers=%d",
        repo_json["full_name"],
        project_meta["stars"],
        owner_json["login"],
        owner_meta["followers"],
    )
