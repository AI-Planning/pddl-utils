
import itertools

def grounding_combos(variables, type2objs):
    """
    Generate all possible combinations of objects for a set of variables.

    Parameters
    ----------
    variables : list
        List of variables to ground.
    type2objs : dict
        Mapping from type to list of objects.

    Returns
    -------
    list
        List of dictionaries mapping variables to objects.
    """
    obj_options = [] #type2objs[var.type_tag] for var in variables]
    for var in variables:
        obj_options.append(set())
        for t in var.type_tags:
            obj_options[-1].update(type2objs[t])
    return [dict(zip(variables, objs)) for objs in itertools.product(*obj_options)]
