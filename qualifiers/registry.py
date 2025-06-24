PLUGINS = []

def qualifier(predicate):
    def _wrap(fn):
        PLUGINS.append((predicate, fn))
        return fn
    return _wrap