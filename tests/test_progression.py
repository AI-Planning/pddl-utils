from pddl.core import Action, And, Predicate
from pddl.logic.base import Not
from pddl.logic.helpers import constants, variables

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
