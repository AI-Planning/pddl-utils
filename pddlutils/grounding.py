
from pddl.logic import Predicate
from pddl.logic.base import BinaryOp, UnaryOp
from pddl.core import Action, Domain, Problem

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

def _recursive_ground(lifted, var2arg):
    if isinstance(lifted, Predicate):
        args = [var2arg[term] for term in lifted.terms]
        return _ground_predicate(lifted, args)
    elif isinstance(lifted, BinaryOp):
        return lifted.__class__(*[_recursive_ground(l, var2arg) for l in lifted.operands])
    elif isinstance(lifted, UnaryOp):
        return lifted.__class__(_recursive_ground(lifted.argument, var2arg))
    else:
        raise NotImplementedError(f"Grounding of {type(lifted)} is not yet implemented")

def _ground_action(action, args):
    """
    Ground an action with the given arguments.

    Parameters
    ----------
    action : Action
        Action to ground.
    args : list
        List of arguments to ground the action with.

    Returns
    -------
    Action
        Grounded action.
    """

    assert len(action.terms) == len(args), "Number of arguments must match"

    for i in range(len(action.terms)):
        assert args[i].type_tag in action.terms[i].type_tags, f"Type of arguments must match: {args[i].type_tag} not in {action.parameters[i].type_tags}"

    var2arg = {var: arg for var, arg in zip(action.parameters, args)}
    aname = action.name + '_' + '_'.join([arg.name for arg in args])
    precond = _recursive_ground(action.precondition, var2arg)
    effect = _recursive_ground(action.effect, var2arg)

    return Action(aname, [], precond, effect)

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
