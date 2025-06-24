import re
from qualifiers.registry import qualifier
from qualifiers.utils import upsert_entity
from common.github import repo, owner
from common.models import ItemEntityMap
RX = re.compile(r'^https://github\.com/(?P<login>[^/]+)/(?P<repo>[^/]+)$')

@qualifier(lambda raw: bool(RX.match(raw.url)))
def enrich(raw, s):
    m = RX.match(raw.url)
    login, repo_name = m['login'], m['repo']
    repo_js  = repo(login, repo_name)
    owner_js = owner(login)

    proj_id = upsert_entity(
        s, repo_name, 'project', raw.url,
        {'stars': repo_js['stargazers_count']}
    )
    own_id  = upsert_entity(
        s, owner_js.get('name') or login,
        'company' if owner_js['type'] == 'Organization' else 'person',
        f'https://github.com/{login}',
        {'followers': owner_js['followers']}
    )
    s.add_all([
        ItemEntityMap(raw_id=raw.id, entity_id=proj_id, confidence=0.98),
        ItemEntityMap(raw_id=raw.id, entity_id=own_id,  confidence=0.95),
    ])