import pytest
from pddl.logic import Predicate
from pddl.logic.terms import Constant
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser

import pddlutils as pu

REQUIREMENTS = "(:requirements :strips :typing :negative-preconditions :equality)"

DOMAIN_TEXT = f"""
(define (domain logistics)
  {REQUIREMENTS}
  (:types vehicle place - object
          truck - vehicle)
  (:constants depot - place)
  (:predicates (at ?v - vehicle ?p - place) (road ?a ?b - place) (ready))
  (:action drive
    :parameters (?v - vehicle ?from ?to - place)
    :precondition (and (at ?v ?from) (road ?from ?to) (not (= ?from ?to)))
    :effect (and (at ?v ?to) (not (at ?v ?from))))
  (:action stay
    :parameters (?v - truck ?p - place)
    :precondition (at ?v ?p)
    :effect (ready))
  (:action reset
    :parameters ()
    :precondition (ready)
    :effect (not (ready))))
"""

PROBLEM_TEXT = f"""
(define (problem small)
  (:domain logistics)
  {REQUIREMENTS}
  (:objects t1 - truck v1 - vehicle l1 - place)
  (:init (at t1 l1) (road l1 depot) (road l1 l1) (not (ready)))
  (:goal (and (at t1 depot) (not (ready)))))
"""


def make_task(domain=DOMAIN_TEXT, problem=PROBLEM_TEXT):
    return pu.Task(DomainParser()(domain), ProblemParser()(problem))


def constant(name, type_tag):
    return Constant(name, type_tag=type_tag)


T1 = constant("t1", "truck")
L1 = constant("l1", "place")
DEPOT = constant("depot", "place")


def signature(action):
    return (action.name, *[term.name for term in action.parameters])


def test_objects_are_problem_objects_and_domain_constants_in_sorted_order():
    assert [obj.name for obj in make_task().objects] == ["depot", "l1", "t1", "v1"]


def test_object_repeating_a_constant_with_the_same_type_is_merged():
    problem = PROBLEM_TEXT.replace("l1 - place)", "l1 depot - place)")

    assert [obj.name for obj in make_task(problem=problem).objects] == [
        "depot",
        "l1",
        "t1",
        "v1",
    ]


def test_object_repeating_a_constant_with_another_type_is_an_error():
    problem = PROBLEM_TEXT.replace("t1 - truck", "t1 depot - truck")

    with pytest.raises(pu.PDDLLogicError, match="depot"):
        make_task(problem=problem)


def test_initial_state_holds_only_true_atoms():
    assert make_task().initial_state == {
        Predicate("at", T1, L1),
        Predicate("road", L1, DEPOT),
        Predicate("road", L1, L1),
    }


def test_ground_looks_up_actions_and_objects_by_name():
    action = make_task().ground("drive", "t1", "l1", "depot")

    assert signature(action) == ("drive", "t1", "l1", "depot")


@pytest.mark.parametrize(
    "step",
    [
        ("fly", "t1"),
        ("drive", "t1", "l1"),
        ("drive", "t1", "l1", "nowhere"),
        ("drive", "l1", "l1", "depot"),
        ("stay", "v1", "l1"),
    ],
)
def test_ground_rejects_invalid_steps(step):
    with pytest.raises(pu.PDDLLogicError):
        make_task().ground(*step)


def test_applicable_actions_in_the_initial_state():
    task = make_task()

    assert [signature(a) for a in task.applicable_actions(task.initial_state)] == [
        ("drive", "t1", "l1", "depot"),
        ("stay", "t1", "l1"),
    ]


def test_applicable_actions_include_parameterless_actions():
    task = make_task()

    assert [signature(a) for a in task.applicable_actions({Predicate("ready")})] == [
        ("reset",)
    ]


def test_applicable_actions_is_empty_at_a_dead_end():
    assert make_task().applicable_actions(frozenset()) == []


def test_applicable_actions_allow_one_object_in_several_parameters():
    domain = f"""
    (define (domain pairs)
      {REQUIREMENTS}
      (:types item)
      (:predicates (ready))
      (:action pair :parameters (?a ?b - item) :precondition (ready) :effect (ready)))
    """
    problem = """
    (define (problem two) (:domain pairs)
      (:objects x y - item) (:init (ready)) (:goal (ready)))
    """
    task = make_task(domain, problem)

    assert [signature(a) for a in task.applicable_actions(task.initial_state)] == [
        ("pair", "x", "x"),
        ("pair", "x", "y"),
        ("pair", "y", "x"),
        ("pair", "y", "y"),
    ]


def test_order_uses_case_sensitive_code_points():
    domain = f"""
    (define (domain cased)
      {REQUIREMENTS}
      (:types item)
      (:predicates (ready))
      (:action b :parameters (?x - item) :precondition (ready) :effect (ready))
      (:action C :parameters (?x - item) :precondition (ready) :effect (ready)))
    """
    problem = """
    (define (problem names) (:domain cased)
      (:objects a B - item) (:init (ready)) (:goal (ready)))
    """
    task = make_task(domain, problem)

    assert [signature(a) for a in task.applicable_actions(task.initial_state)] == [
        ("C", "B"),
        ("C", "a"),
        ("b", "B"),
        ("b", "a"),
    ]


def test_ground_atoms_cover_every_type_consistent_atom_in_sorted_order():
    atoms = make_task().ground_atoms()

    assert [(atom.name, *[t.name for t in atom.terms]) for atom in atoms] == [
        ("at", "t1", "depot"),
        ("at", "t1", "l1"),
        ("at", "v1", "depot"),
        ("at", "v1", "l1"),
        ("ready",),
        ("road", "depot", "depot"),
        ("road", "depot", "l1"),
        ("road", "l1", "depot"),
        ("road", "l1", "l1"),
    ]


def test_progress_and_is_applicable_use_ground_actions():
    task = make_task()
    drive = task.ground("drive", "t1", "l1", "depot")

    assert task.is_applicable(task.initial_state, drive)
    assert Predicate("at", T1, DEPOT) in task.progress(task.initial_state, drive)


def test_is_goal():
    task = make_task()

    assert not task.is_goal(task.initial_state)
    assert task.is_goal({Predicate("at", T1, DEPOT)})
    assert not task.is_goal({Predicate("at", T1, DEPOT), Predicate("ready")})


def test_actions_outside_the_fragment_are_rejected_by_name():
    domain = """
    (define (domain choice)
      (:requirements :strips :disjunctive-preconditions)
      (:predicates (p) (q))
      (:action pick :parameters () :precondition (or (p) (q)) :effect (q)))
    """
    problem = "(define (problem one) (:domain choice) (:init (p)) (:goal (q)))"

    with pytest.raises(NotImplementedError, match="pick"):
        make_task(domain, problem)


def test_task_loads_domain_and_problem_from_files(tmp_path):
    domain_file = tmp_path / "domain.pddl"
    problem_file = tmp_path / "problem.pddl"
    domain_file.write_text(DOMAIN_TEXT)
    problem_file.write_text(PROBLEM_TEXT)

    task = pu.Task(str(domain_file), str(problem_file))

    assert len(task.objects) == 4
