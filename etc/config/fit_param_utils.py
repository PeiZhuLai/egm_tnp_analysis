import re


def params_with_updates(base_params, *updated_params):
    """Return a copied parameter list with named RooFactory entries replaced."""
    params = list(base_params)
    for updated in updated_params:
        match = re.match(r'^([A-Za-z_][A-Za-z0-9_]*)\[', updated.strip())
        if not match:
            raise ValueError('Parameter update must look like name[...] : %s' % updated)
        name = match.group(1)
        prefix = '%s[' % name
        params = [item for item in params if not str(item).startswith(prefix)]
        params.append(updated)
    return params
