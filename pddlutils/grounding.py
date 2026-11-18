
from pddl.logic import Predicate
from pddl.core import Action, Domain, Problem

from pddlutils.exceptions import PDDLLogicError

def ground(lifted, *args, domain=None):
    """
    Ground a lifted domain, action, or predicate with the given arguments.

    Parameters
    ----------
    lifted : Action or Predicate
        Lifted action or predicate to ground.
    args : list
        List of arguments to ground the lifted action or predicate with.
    domain : Domain
        Domain whose type hierarchy the arguments are checked against.
        Required when grounding an action or predicate.

    Returns
    -------
    Action or Predicate
        Grounded domain, action, or predicate.

    Raises
    ------
    PDDLLogicError
        If the arguments don't fit the parameters in number or type.
    """

    if isinstance(lifted, (Action, Predicate)) and domain is None:
        raise TypeError("Grounding an action or predicate requires the domain")

    if isinstance(lifted, Action):
        return _ground_action(lifted, args, domain)
    elif isinstance(lifted, Predicate):
        return _ground_predicate(lifted, args, domain)
    elif isinstance(lifted, Domain):
        assert len(args) == 1 and isinstance(args[0], Problem), "A domain must be grounded with a problem"
        raise NotImplementedError("Grounding of a domain is not yet implemented")
    else:
        raise ValueError("Unknown type of lifted object")

def has_type(obj, term, domain):
    """Check whether an object can fill a parameter, given the type hierarchy."""
    allowed = term.type_tags
    if not allowed or "object" in allowed:
        return True

    current = obj.type_tag
    seen = set()
    while current is not None and current not in seen:
        if current in allowed:
            return True
        seen.add(current)
        current = domain.types.get(current)
    return False

def _check_arguments(name, terms, args, domain):
    if len(terms) != len(args):
        raise PDDLLogicError(f"{name} takes {len(terms)} arguments, but got {len(args)}")

    for term, arg in zip(terms, args):
        if not has_type(arg, term, domain):
            raise PDDLLogicError(
                f"{name}: object {arg.name} of type {arg.type_tag} can't fill "
                f"{term} of type {sorted(term.type_tags)}"
            )

def _ground_action(action, args, domain):
    """
    Ground an action with the given arguments.

    Parameters
    ----------
    action : Action
        Action to ground.
    args : list
        List of arguments to ground the action with.
    domain : Domain
        Domain whose type hierarchy the arguments are checked against.

    Returns
    -------
    Action
        Grounded action.
    """

    _check_arguments(action.name, action.parameters, args, domain)

    return action.instantiate(list(args))

def _ground_predicate(predicate, args, domain):
    """
    Ground a predicate with the given arguments.

    Parameters
    ----------
    predicate : Predicate
        Predicate to ground.
    args : list
        List of arguments to ground the predicate with.
    domain : Domain
        Domain whose type hierarchy the arguments are checked against.

    Returns
    -------
    Predicate
        Grounded predicate.
    """

    _check_arguments(predicate.name, predicate.terms, args, domain)

    return Predicate(predicate.name, *args)
