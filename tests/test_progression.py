import pytest
from pddl.core import Action, And, Predicate
from pddl.logic.base import Not
from pddl.logic.helpers import constants, variables
from pddl.logic.predicates import EqualTo

from pddlutils.exceptions import PDDLLogicError
from pddlutils.progression import progress


def test_simple():
    x, y = variables("x y")
    p_on = Predicate("on", x, y)
    p_holding = Predicate("holding", x)
    a_pick_up = Action(
        name="pick-up",
        parameters=[x, y],
        precondition=p_on(x, y),
        effect=And(p_holding(x), Not(p_on(x, y))),
    )

    a, b, c = constants("a b c")
    state = {p_on(a, b), p_on(b, c)}
    action = a_pick_up.instantiate([a, b])

    succ_state = progress(state, action)
    succ_state_expected = {p_holding(a), p_on(b, c)}
    assert succ_state == succ_state_expected


def _move_action():
    a, b = variables("a b")
    at = Predicate("at", a)
    return Action(
        name="move",
        parameters=[a, b],
        precondition=And(at, Not(EqualTo(a, b))),
        effect=And(Predicate("at", b), Not(at)),
    )


def test_inequality_precondition_holds_for_distinct_objects():
    l1, l2 = constants("l1 l2")
    action = _move_action().instantiate([l1, l2])

    assert progress({Predicate("at", l1)}, action) == {Predicate("at", l2)}


def test_inequality_precondition_fails_for_the_same_object():
    l1 = constants("l1")[0]
    action = _move_action().instantiate([l1, l1])

    with pytest.raises(PDDLLogicError):
        progress({Predicate("at", l1)}, action)


def test_positive_equality_precondition():
    a, b = variables("a b")
    action = Action("same", [a, b], precondition=EqualTo(a, b), effect=Predicate("done"))
    l1, l2 = constants("l1 l2")

    assert progress(set(), action.instantiate([l1, l1])) == {Predicate("done")}
    with pytest.raises(PDDLLogicError):
        progress(set(), action.instantiate([l1, l2]))


def test_equality_in_an_effect_is_not_strips():
    a, b = variables("a b")
    action = Action("bad", [a, b], precondition=None, effect=EqualTo(a, b))
    l1, l2 = constants("l1 l2")

    with pytest.raises(NotImplementedError):
        progress(set(), action.instantiate([l1, l2]))
