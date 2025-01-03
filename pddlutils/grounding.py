
from pddl.logic import Predicate
from pddl.logic.base import BinaryOp, UnaryOp, ForallCondition, ExistsCondition, And, Or, QuantifiedCondition
from pddl.core import Action, Domain, Problem

from pddlutils.utils import grounding_combos

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

def unquantify(action, objs):
    """
    Unquantify an action with the given objects. I.e., convert forall to "and", and exists to "or".

    Parameters
    ----------
    action : Action
        Action to unquantify.
    objs : list
        List of objects to unquantify the action with.

    Returns
    -------
    Action
        Unquantified action.
    """

    type2objs = {}
    for obj in objs:
        if obj.type_tag not in type2objs:
            type2objs[obj.type_tag] = []
        type2objs[obj.type_tag].append(obj)
    import pprint
    def _recursive_unquantify(lifted, var2arg):
        if isinstance(lifted, ForallCondition):
            new_var2arg = var2arg.copy()
            instantiations = []
            for g in grounding_combos(lifted.variables, type2objs):
                for v in g:
                    new_var2arg[str(v)] = g[v]
                instantiations.append(_recursive_unquantify(lifted.condition, new_var2arg))
            return And(*instantiations)
        elif isinstance(lifted, ExistsCondition):
            new_var2arg = var2arg.copy()
            instantiations = []
            for g in grounding_combos(lifted.variables, type2objs):
                for v in g:
                    new_var2arg[str(v)] = g[v]
                instantiations.append(_recursive_unquantify(lifted.condition, new_var2arg))
            return Or(*instantiations)
        elif isinstance(lifted, BinaryOp):
            return lifted.__class__(*[_recursive_unquantify(l, var2arg) for l in lifted.operands])
        elif isinstance(lifted, UnaryOp):
            return lifted.__class__(_recursive_unquantify(lifted.argument, var2arg))
        elif isinstance(lifted, Predicate):
            args = [var2arg.get(str(term), term) for term in lifted.terms]
            return Predicate(lifted.name, *args)
        else:
            raise NotImplementedError(f"Unquantification of {type(lifted)} is not yet implemented")

    return Action(action.name, action.parameters, _recursive_unquantify(action.precondition, {}), _recursive_unquantify(action.effect, {}))

def _recursive_ground(lifted, var2arg):
    if isinstance(lifted, Predicate):
        args = [var2arg.get(term, term) for term in lifted.terms]
        return _ground_predicate(lifted, args)
    elif isinstance(lifted, BinaryOp):
        return lifted.__class__(*[_recursive_ground(l, var2arg) for l in lifted.operands])
    elif isinstance(lifted, UnaryOp):
        return lifted.__class__(_recursive_ground(lifted.argument, var2arg))
    elif isinstance(lifted, QuantifiedCondition):
        raise ValueError("Cannot ground quantified condition -- run unquantify first on the action")
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
