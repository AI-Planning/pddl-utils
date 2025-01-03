
from pddl.logic import Predicate
from pddl.core import Action
from pddl.core import Domain, Problem

def ground(lifted, *args):
    """
    Ground a lifted domain, action, or predicate with the given arguments.

    Parameters
    ----------
    lifted : Action or Predicate
        Lifted action or predicate to ground.
    args : list
        List of arguments to ground the lifted action or predicate with.

    Returns
    -------
    Action or Predicate
        Grounded domain, action, or predicate.
    """

    if isinstance(lifted, Action):
        return _ground_action(lifted, args)
    elif isinstance(lifted, Predicate):
        return _ground_predicate(lifted, args)
    elif isinstance(lifted, Domain):
        assert len(args) == 1 and isinstance(args[0], Problem), "A domain must be grounded with a problem"
        raise NotImplementedError("Grounding of a domain is not yet implemented")
    else:
        raise ValueError("Unknown type of lifted object")

def _ground_action(action, args):
    raise NotImplementedError("Grounding of actions is not yet implemented")

def _ground_predicate(predicate, args):
    """
    Ground a predicate with the given arguments.

    Parameters
    ----------
    predicate : Predicate
        Predicate to ground.
    args : list
        List of arguments to ground the predicate with.

    Returns
    -------
    Predicate
        Grounded predicate.
    """

    assert predicate.arity == len(args), "Number of arguments must match"

    for i in range(predicate.arity):
        assert args[i].type_tag in predicate.terms[i].type_tags, f"Type of arguments must match: {args[i].type_tag} not in {predicate.terms[i].type_tags}"

    return Predicate(predicate.name, *args)
