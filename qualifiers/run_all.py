import importlib
import pkgutil
import logging
from sqlalchemy import text

from common.db import get_session

logger = logging.getLogger(__name__)

import qualifiers as _pkg  # the package object, has __path__

for mod in pkgutil.walk_packages(_pkg.__path__, prefix=_pkg.__name__ + "."):
    # skip helper modules and this runner itself
    if mod.name.endswith(("registry", "utils", "run_all")):
        continue
    importlib.import_module(mod.name)
    logger.debug("Imported plug-in module %s", mod.name)

# now PLUGINS is populated
from qualifiers.registry import PLUGINS

logger.info("Loaded %d plug-ins: %s",
            len(PLUGINS),
            [fn.__module__ for _, fn in PLUGINS])


with get_session() as s:
    rows = s.execute(text(
        "select * from raw_items r "
        "where not exists (select 1 from item_entity_map m where m.raw_id = r.id)"
        "limit 500"
    )).mappings().all()

    for raw in rows:
        for pred, fn in PLUGINS:
            if pred(raw):
                fn(raw, s)
    s.commit()