from typing import Optional

from pddl.core import Action, And, Formula, Predicate
from pddl.logic.base import Not

from pddlutils.types import Literal


def is_neg_literal(literal: Formula) -> bool:
    return isinstance(literal, Not) and isinstance(literal.argument, Predicate)


def is_pos_literal(literal: Formula) -> bool:
    return isinstance(literal, Predicate)


def is_literal(formula: Formula) -> bool:
    return is_pos_literal(formula) or is_neg_literal(formula)


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
    """Check precondition and effects are conjuncts of literals"""
    try:
        get_strips_literal_list(action.precondition)
        get_strips_literal_list(action.effect)
        return True
    except ValueError:
        return False
