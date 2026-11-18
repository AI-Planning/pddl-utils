import random
from itertools import product

import pytest
from pddl.action import Action
from pddl.parser.domain import DomainParser
from pddl.parser.problem import ProblemParser

import pddlutils as pu

REQUIREMENTS = "(:requirements :strips :typing :negative-preconditions :equality)"

DOMAIN_TEXT = f"""
(define (domain fragment)
  {REQUIREMENTS}
  (:types vehicle place - object
          truck - vehicle)
  (:constants depot - place)
  (:predicates (at ?v - vehicle ?p - place)
               (road ?a ?b - place)
               (closed ?p - place)
               (ready))
  (:action drive
    :parameters (?v - vehicle ?from ?to - place)
    :precondition (and (at ?v ?from) (road ?from ?to) (not (= ?from ?to))
                       (not (closed ?to)))
    :effect (and (at ?v ?to) (not (at ?v ?from))))
  (:action loop
    :parameters (?p - place)
    :precondition (road ?p ?p)
    :effect (closed ?p))
  (:action same
    :parameters (?a ?b - place)
    :precondition (= ?a ?b)
    :effect (ready))
  (:action unload
    :parameters (?v - truck)
    :precondition (at ?v depot)
    :effect (ready))
  (:action open-any
    :parameters (?p - place ?v - vehicle)
    :precondition (not (closed ?p))
    :effect (closed ?p))
  (:action anything
    :parameters (?v - truck ?p - place)
    :precondition ()
    :effect (ready))
  (:action reset
    :parameters ()
    :precondition (ready)
    :effect (not (ready))))
"""

PROBLEM_TEXT = f"""
(define (problem small)
  (:domain fragment)
  {REQUIREMENTS}
  (:objects t1 - truck v1 - vehicle l1 l2 - place)
  (:init (at t1 l1) (at v1 l2) (road l1 l2) (road l2 depot) (road l1 l1))
  (:goal (ready)))
"""

CHAIN_DOMAIN = f"""
(define (domain chain)
  {REQUIREMENTS}
  (:predicates (link ?a ?b))
  (:action hop
    :parameters (?a ?b ?c ?d)
    :precondition (and (link ?a ?b) (link ?b ?c) (link ?c ?d))
    :effect (not (link ?a ?b))))
"""


def chain_problem(size):
    names = [f"n{index:02}" for index in range(size)]
    links = " ".join(f"(link {a} {b})" for a, b in zip(names, names[1:]))
    return f"""
    (define (problem chain-{size})
      (:domain chain)
      {REQUIREMENTS}
      (:objects {' '.join(names)})
      (:init {links})
      (:goal (link n00 n01)))
    """


def make_task(domain=DOMAIN_TEXT, problem=PROBLEM_TEXT):
    return pu.Task(DomainParser()(domain), ProblemParser()(problem))


def signature(action):
    return (str(action.name), *[str(term.name) for term in action.parameters])


def every_applicable_action(task, state):
    """List applicable ground actions by trying every type-consistent grounding."""
    applicable = []
    for action in sorted(task.domain.actions, key=lambda a: str(a.name)):
        for arguments in product(
            *[
                [obj for obj in task.objects if pu.grounding.has_type(obj, term, task.domain)]
                for term in action.parameters
            ]
        ):
            grounded = action.instantiate(list(arguments))
            if task.is_applicable(state, grounded):
                applicable.append(signature(grounded))
    return applicable


def test_lists_the_same_actions_in_the_same_order_as_trying_every_grounding():
    task = make_task()
    atoms = task.ground_atoms()
    generator = random.Random(0)

    states = [task.initial_state, frozenset(), frozenset(atoms)]
    states += [
        frozenset(generator.sample(atoms, generator.randrange(len(atoms) + 1)))
        for _ in range(200)
    ]

    for state in states:
        listed = [signature(action) for action in task.applicable_actions(state)]
        assert listed == every_applicable_action(task, state)


def test_listed_actions_can_be_applied():
    task = make_task()

    for action in task.applicable_actions(task.initial_state):
        task.progress(task.initial_state, action)


def test_only_groundings_matching_the_state_are_built(monkeypatch):
    task = make_task(CHAIN_DOMAIN, chain_problem(12))
    built = []
    instantiate = Action.instantiate

    def counting_instantiate(self, *args, **kwargs):
        built.append(self.name)
        return instantiate(self, *args, **kwargs)

    monkeypatch.setattr(Action, "instantiate", counting_instantiate)

    applicable = task.applicable_actions(task.initial_state)

    assert len(applicable) == 9
    assert len(built) == len(applicable)


@pytest.mark.parametrize("size", [2, 3])
def test_no_action_is_listed_when_preconditions_cannot_chain(size):
    task = make_task(CHAIN_DOMAIN, chain_problem(size))

    assert task.applicable_actions(task.initial_state) == []
