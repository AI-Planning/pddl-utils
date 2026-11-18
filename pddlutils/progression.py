from pddl.action import Action, Optional
from pddl.logic import Predicate
from pddl.logic.base import And, Formula, Not
from pddl.logic.predicates import EqualTo

from pddlutils.exceptions import PDDLLogicError
from pddlutils.strips import get_precondition, is_strips_action
from pddlutils.types import State


def satisfies(state: State, formula: Optional[Formula]) -> bool:
    """Check if a state satisfies a formula"""
    if formula is None:
        return True
    elif isinstance(formula, And):
        return all(satisfies(state, subformula) for subformula in formula.operands)
    elif isinstance(formula, Not):
        return not satisfies(state, formula.argument)
    elif isinstance(formula, Predicate):
        return formula in state
    elif isinstance(formula, EqualTo):
        return formula.left == formula.right
    else:
        raise NotImplementedError(f"Unsupported formula type: {type(formula)}")


def _effect_literals(effects: Optional[Formula]) -> tuple[set, set]:
    """Split effects into the atoms they add and the atoms they delete"""
    if effects is None:
        return set(), set()
    elif isinstance(effects, Predicate):
        return {effects}, set()
    elif isinstance(effects, Not) and isinstance(effects.argument, Predicate):
        return set(), {effects.argument}
    elif isinstance(effects, And):
        adds, deletes = set(), set()
        for effect in effects.operands:
            effect_adds, effect_deletes = _effect_literals(effect)
            adds |= effect_adds
            deletes |= effect_deletes
        return adds, deletes
    else:
        raise NotImplementedError(f"Unsupported effects type: {type(effects)}")


def apply_effects(state: State, effects: Optional[Formula]) -> State:
    """Apply effects to a state, with deletes applied before adds"""
    adds, deletes = _effect_literals(effects)
    return (state - deletes) | adds


def is_applicable(state: State, action: Action) -> bool:
    """Check if a ground action applies in a state"""
    if not is_strips_action(action):
        raise NotImplementedError(
            "Applicability is currently only supported for STRIPS actions."
        )
    return satisfies(state, get_precondition(action))


def progress(state: State, action: Action) -> State:
    """Progress an action"""
    if not is_applicable(state, action):
        raise PDDLLogicError("Action precondition is not satisfied in the state.")
    return apply_effects(state, action.effect)
