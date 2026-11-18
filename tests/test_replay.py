import pytest
from pddl.logic import Predicate
from pddl.logic.terms import Constant
from pddl.parser.domain import DomainParser
from pddl.parser.plan import PlanParser
from pddl.parser.problem import ProblemParser

import pddlutils as pu

REQUIREMENTS = "(:requirements :strips :typing :negative-preconditions :equality)"

DOMAIN = DomainParser()(
    f"""
    (define (domain walk)
      {REQUIREMENTS}
      (:types person place)
      (:predicates (at ?w - person ?p - place))
      (:action go
        :parameters (?w - person ?a ?b - place)
        :precondition (and (at ?w ?a) (not (= ?a ?b)))
        :effect (and (at ?w ?b) (not (at ?w ?a)))))
    """
)
PROBLEM = ProblemParser()(
    f"""
    (define (problem trip)
      (:domain walk)
      {REQUIREMENTS}
      (:objects w - person a b c - place)
      (:init (at w a))
      (:goal (at w c)))
    """
)

W = Constant("w", type_tag="person")


def at(place):
    return Predicate("at", W, Constant(place, type_tag="place"))


@pytest.fixture
def task():
    return pu.Task(DOMAIN, PROBLEM)


def test_valid_plan_reaching_the_goal(task):
    result = task.replay(PlanParser()("(go w a b)\n(go w b c)\n"))

    assert result.states == ({at("a")}, {at("b")}, {at("c")})
    assert result.succeeded
    assert result.failed_step is None
    assert result.failure_reason is None
    assert result.goal_reached


def test_valid_plan_missing_the_goal(task):
    result = task.replay(PlanParser()("(go w a b)\n"))

    assert result.succeeded
    assert not result.goal_reached


def test_empty_plan_stays_in_the_initial_state(task):
    result = task.replay([])

    assert result.states == ({at("a")},)
    assert result.succeeded
    assert not result.goal_reached


def test_sequence_of_ground_actions(task):
    plan = [task.ground("go", "w", "a", "b"), task.ground("go", "w", "b", "c")]

    result = task.replay(plan)

    assert result.states[-1] == {at("c")}
    assert result.goal_reached


def test_replay_stops_at_the_first_unmet_precondition(task):
    result = task.replay(PlanParser()("(go w a b)\n(go w a c)\n(go w b c)\n"))

    assert result.states == ({at("a")}, {at("b")})
    assert not result.succeeded
    assert result.failed_step == 1
    assert "(go w a c)" in result.failure_reason
    assert not result.goal_reached


@pytest.mark.parametrize(
    ("step", "reason"),
    [
        ("(fly w a b)", "Unknown action"),
        ("(go w a)", "arguments"),
        ("(go w a nowhere)", "Unknown object"),
        ("(go a a b)", "can't fill"),
        ("(go w a a)", "precondition"),
    ],
)
def test_invalid_steps_are_reported_without_raising(task, step, reason):
    result = task.replay(PlanParser()(f"{step}\n"))

    assert result.states == ({at("a")},)
    assert result.failed_step == 0
    assert reason in result.failure_reason
