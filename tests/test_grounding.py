import pytest
from pddl.logic import Predicate
from pddl.logic.terms import Constant
from pddl.parser.domain import DomainParser

import pddlutils as pu
from pddlutils.exceptions import PDDLLogicError

REQUIREMENTS = "(:requirements :strips :typing :negative-preconditions :equality)"

DOMAIN = DomainParser()(
    f"""
    (define (domain logistics)
      {REQUIREMENTS}
      (:types vehicle place - object
              truck - vehicle
              pickup - truck)
      (:constants depot - place)
      (:predicates (at ?v - vehicle ?p - place) (ready))
      (:action drive
        :parameters (?v - vehicle ?from ?to - place)
        :precondition (at ?v ?from)
        :effect (and (at ?v ?to) (not (at ?v ?from))))
      (:action either-kind
        :parameters (?x - (either truck place))
        :precondition (ready)
        :effect (not (ready))))
    """
)
ACTIONS = {action.name: action for action in DOMAIN.actions}
PREDICATES = {predicate.name: predicate for predicate in DOMAIN.predicates}

TRUCK = Constant("t1", type_tag="truck")
PICKUP = Constant("p1", type_tag="pickup")
VEHICLE = Constant("v1", type_tag="vehicle")
L1 = Constant("l1", type_tag="place")
L2 = Constant("l2", type_tag="place")


@pytest.mark.parametrize("vehicle", [VEHICLE, TRUCK, PICKUP])
def test_action_accepts_a_type_or_any_of_its_subtypes(vehicle):
    ground = pu.ground(ACTIONS["drive"], vehicle, L1, L2, domain=DOMAIN)

    assert ground.precondition == Predicate("at", vehicle, L1)


def test_action_rejects_an_unrelated_type():
    with pytest.raises(PDDLLogicError, match="l2"):
        pu.ground(ACTIONS["drive"], L2, L1, L2, domain=DOMAIN)


def test_action_rejects_a_supertype_of_the_parameter():
    with pytest.raises(PDDLLogicError):
        pu.ground(ACTIONS["either-kind"], VEHICLE, domain=DOMAIN)


@pytest.mark.parametrize("argument", [TRUCK, PICKUP, L1])
def test_action_accepts_any_branch_of_an_either_type(argument):
    pu.ground(ACTIONS["either-kind"], argument, domain=DOMAIN)


def test_action_rejects_the_wrong_number_of_arguments():
    with pytest.raises(PDDLLogicError):
        pu.ground(ACTIONS["drive"], TRUCK, L1, domain=DOMAIN)


def test_predicate_accepts_a_subtype():
    atom = pu.ground(PREDICATES["at"], PICKUP, L1, domain=DOMAIN)

    assert atom == Predicate("at", PICKUP, L1)


def test_predicate_rejects_an_unrelated_type():
    with pytest.raises(PDDLLogicError):
        pu.ground(PREDICATES["at"], L1, L2, domain=DOMAIN)


def test_untyped_parameters_accept_any_object():
    domain = DomainParser()(
        """
        (define (domain untyped)
          (:requirements :strips)
          (:predicates (on ?x))
          (:action lift :parameters (?x) :precondition (on ?x) :effect (not (on ?x))))
        """
    )
    action = next(iter(domain.actions))

    pu.ground(action, Constant("anything"), domain=domain)
    pu.ground(action, Constant("typed", type_tag="whatever"), domain=domain)


def test_grounding_requires_the_domain():
    with pytest.raises(TypeError):
        pu.ground(ACTIONS["drive"], TRUCK, L1, L2)


def test_action_without_a_precondition():
    domain = DomainParser()(
        f"""
        (define (domain open)
          {REQUIREMENTS}
          (:types place)
          (:predicates (visited ?p - place))
          (:action visit :parameters (?p - place) :effect (visited ?p)))
        """
    )

    ground = pu.ground(next(iter(domain.actions)), L1, domain=domain)

    assert ground.precondition is None
    assert ground.effect == Predicate("visited", L1)


def test_action_that_mentions_a_domain_constant():
    domain = DomainParser()(
        f"""
        (define (domain depot)
          {REQUIREMENTS}
          (:types truck place)
          (:constants depot - place)
          (:predicates (at ?t - truck ?p - place))
          (:action leave
            :parameters (?t - truck ?p - place)
            :precondition (at ?t depot)
            :effect (and (at ?t ?p) (not (at ?t depot)))))
        """
    )
    depot = Constant("depot", type_tag="place")

    ground = pu.ground(next(iter(domain.actions)), TRUCK, L1, domain=domain)

    assert ground.precondition == Predicate("at", TRUCK, depot)


def test_ground_action_keeps_its_name_and_objects():
    ground = pu.ground(ACTIONS["drive"], TRUCK, L1, L2, domain=DOMAIN)

    assert ground.name == "drive"
    assert ground.parameters == (TRUCK, L1, L2)


def test_ground_actions_with_similar_object_names_stay_distinct():
    first = pu.ground(
        ACTIONS["drive"],
        Constant("a_b", type_tag="truck"),
        Constant("c", type_tag="place"),
        L1,
        domain=DOMAIN,
    )
    second = pu.ground(
        ACTIONS["drive"],
        Constant("a", type_tag="truck"),
        Constant("b_c", type_tag="place"),
        L1,
        domain=DOMAIN,
    )

    assert first.parameters != second.parameters
    assert first != second


def test_action_with_an_inequality_precondition():
    domain = DomainParser()(
        f"""
        (define (domain distinct)
          {REQUIREMENTS}
          (:types place)
          (:predicates (at ?p - place))
          (:action go
            :parameters (?a ?b - place)
            :precondition (and (at ?a) (not (= ?a ?b)))
            :effect (and (at ?b) (not (at ?a)))))
        """
    )

    ground = pu.ground(next(iter(domain.actions)), L1, L2, domain=domain)

    assert pu.progress({Predicate("at", L1)}, ground) == {Predicate("at", L2)}
