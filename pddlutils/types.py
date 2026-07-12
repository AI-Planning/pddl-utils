from typing import AbstractSet, Union

from pddl.core import Formula, Predicate
from pddl.logic.base import Not

__all__ = ["Literal", "State"]

Literal = Union[Predicate, Not]
State = AbstractSet[Formula]
