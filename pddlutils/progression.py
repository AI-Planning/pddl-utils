from pddl.action import Action, Optional
from pddl.logic import Predicate
from pddl.logic.base import And, Formula, Not
from pddl.logic.predicates import EqualTo

from pddlutils.exceptions import PDDLLogicError
from pddlutils.strips import is_strips_action
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


def apply_effects(state: State, effects: Optional[Formula]) -> State:
    """Apply effects to a state"""
    if isinstance(effects, Predicate):
        return state | {effects}
    elif isinstance(effects, Not):
        return state - {effects.argument}
    elif isinstance(effects, And):
        for effect in effects.operands:
            state = apply_effects(state, effect)
        return state
    else:
        raise NotImplementedError(f"Unsupported effects type: {type(effects)}")


def progress(state: State, action: Action) -> State:
    """Progress an action"""
    if not is_strips_action(action):
        raise NotImplementedError(
            "Progression is currently only supported for STRIPS actions."
        )
    if not satisfies(state, action.precondition):
        raise PDDLLogicError("Action precondition is not satisfied in the state.")
    return apply_effects(state, action.effect)
