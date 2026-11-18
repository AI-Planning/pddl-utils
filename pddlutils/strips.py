from typing import Optional

from pddl.core import Action, And, Formula, Predicate
from pddl.logic.base import Not, Or
from pddl.logic.predicates import EqualTo

from pddlutils.types import Literal


def is_neg_literal(literal: Formula) -> bool:
    return isinstance(literal, Not) and isinstance(literal.argument, Predicate)


def is_pos_literal(literal: Formula) -> bool:
    return isinstance(literal, Predicate)


def is_literal(formula: Formula) -> bool:
    return is_pos_literal(formula) or is_neg_literal(formula)


def is_equality_literal(literal: Formula) -> bool:
    if isinstance(literal, Not):
        return isinstance(literal.argument, EqualTo)
    return isinstance(literal, EqualTo)


def get_precondition(action: Action) -> Optional[Formula]:
    """Get an action's precondition, or None if it is empty

    The pddl library parses `:precondition ()` as a disjunction of nothing,
    which would otherwise be false.
    """
    precondition = action.precondition
    if isinstance(precondition, Or) and not precondition.operands:
        return None
    return precondition


def is_strips_condition(formula: Optional[Formula]) -> bool:
    """Check a formula is a conjunct of literals, which may use equality"""
    if formula is None:
        return True
    conjuncts = formula.operands if isinstance(formula, And) else [formula]
    return all(is_literal(c) or is_equality_literal(c) for c in conjuncts)


def get_strips_literal_list(formula: Optional[Formula]) -> list[Literal]:
    """Get list of literals from a conjunct of literal"""
    if formula is None:
        return []
    elif isinstance(formula, And) and all(is_literal(c) for c in formula.operands):
        return list(formula.operands)
    elif is_literal(formula):
        return [formula]
    else:
        raise ValueError(f"Unsupported input {formula}")


def get_pos_literal_list(formula: Optional[Formula]) -> list[Predicate]:
    """Get list of positive literals from a conjunct of literal"""
    if formula is None:
        return []
    elif isinstance(formula, And) and all(is_literal(c) for c in formula.operands):
        return [c for c in formula.operands if is_pos_literal(c)]
    elif is_pos_literal(formula):
        return [formula]
    else:
        raise ValueError(f"Unsupported input {formula}")


def get_neg_literal_list(formula: Optional[Formula]) -> list[Not]:
    """Get list of negative literals from a conjunct of literal"""
    if formula is None:
        return []
    elif isinstance(formula, And) and all(is_literal(c) for c in formula.operands):
        return [c for c in formula.operands if is_neg_literal(c)]
    elif is_neg_literal(formula):
        return [formula]
    else:
        raise ValueError(f"Unsupported input {formula}")


def is_strips_action(action: Action) -> bool:
    """Check precondition and effects are conjuncts of literals

    Only the precondition may use equality.
    """
    try:
        get_strips_literal_list(action.effect)
    except ValueError:
        return False
    return is_strips_condition(get_precondition(action))
