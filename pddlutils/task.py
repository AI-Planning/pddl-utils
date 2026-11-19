from dataclasses import dataclass
from itertools import product
from typing import Iterable, Optional, Sequence, Union

from pddl import parse_domain, parse_problem
from pddl.action import Action
from pddl.core import Domain, Plan, Problem
from pddl.logic import Predicate
from pddl.logic.base import Not
from pddl.logic.terms import Constant, Variable

from pddlutils.exceptions import PDDLLogicError
from pddlutils.grounding import ground, has_type
from pddlutils.progression import is_applicable, progress, satisfies
from pddlutils.strips import get_precondition, is_strips_action, is_strips_condition
from pddlutils.types import State


@dataclass(frozen=True)
class ReplayResult:
    """The outcome of replaying a plan from a problem's initial state."""

    states: tuple
    """The states visited, starting with the initial state."""
    failed_step: Optional[int]
    """The zero-based index of the first step that failed, if any."""
    failure_reason: Optional[str]
    """Why that step failed, if any did."""
    goal_reached: bool
    """Whether every step succeeded and the final state satisfies the goal."""

    @property
    def succeeded(self) -> bool:
        """Whether every step of the plan could be applied."""
        return self.failed_step is None


class Task:
    """A domain together with one problem to solve in it.

    States are sets of the ground atoms that are true. Actions and atoms are
    listed by name and then object names, in case-sensitive code-point order.
    """

    def __init__(self, domain: Union[Domain, str], problem: Union[Problem, str]):
        """Build a task from parsed objects or paths to PDDL files."""
        self.domain = parse_domain(domain) if isinstance(domain, str) else domain
        self.problem = parse_problem(problem) if isinstance(problem, str) else problem

        self._check_fragment()
        self._actions = {str(action.name): action for action in self.domain.actions}
        self._objects = _merge_objects(self.domain.constants, self.problem.objects)
        self.objects = tuple(self._objects[name] for name in sorted(self._objects))
        self.initial_state = _initial_state(self.problem.init)
        self._allowed = {
            name: {
                str(term.name): dict.fromkeys(
                    str(obj.name)
                    for obj in self.objects
                    if has_type(obj, term, self.domain)
                )
                for term in action.parameters
            }
            for name, action in self._actions.items()
        }

    def _check_fragment(self) -> None:
        for action in self.domain.actions:
            if not is_strips_action(action):
                raise NotImplementedError(
                    f"Action {action.name} is outside the supported STRIPS fragment."
                )
        if not is_strips_condition(self.problem.goal):
            raise NotImplementedError("The goal is outside the supported STRIPS fragment.")

    def ground(self, action: str, *objects: Union[str, Constant]) -> Action:
        """Ground the named action with objects given by name or as constants."""
        if str(action) not in self._actions:
            raise PDDLLogicError(f"Unknown action: {action}")
        arguments = [self._object(obj) for obj in objects]
        return ground(self._actions[str(action)], *arguments, domain=self.domain)

    def _object(self, obj: Union[str, Constant]) -> Constant:
        name = str(obj.name) if isinstance(obj, Constant) else str(obj)
        if name not in self._objects:
            raise PDDLLogicError(f"Unknown object: {name}")
        return self._objects[name]

    def _groundings(self, terms: Sequence) -> Iterable[tuple]:
        """Yield every type-consistent argument tuple, in sorted order."""
        candidates = [
            [obj for obj in self.objects if has_type(obj, term, self.domain)]
            for term in terms
        ]
        return product(*candidates)

    def ground_atoms(self) -> list[Predicate]:
        """List every type-consistent ground atom."""
        predicates = sorted(self.domain.predicates, key=lambda p: str(p.name))
        return [
            Predicate(predicate.name, *arguments)
            for predicate in predicates
            for arguments in self._groundings(predicate.terms)
        ]

    def applicable_actions(self, state: State) -> list[Action]:
        """List the ground actions that apply in a state."""
        facts = _FactIndex(state)
        applicable = []
        for name in sorted(self._actions):
            action = self._actions[name]
            for arguments in self._candidate_arguments(action, facts):
                grounded = action.instantiate(list(arguments))
                if is_applicable(state, grounded):
                    applicable.append(grounded)
        return applicable

    def _candidate_arguments(self, action: Action, facts: "_FactIndex") -> list[tuple]:
        """List argument tuples that satisfy the action's positive preconditions.

        Parameters those preconditions don't mention range over every object of
        their type, so the caller still checks each candidate against the state.
        """
        parameters = [str(term.name) for term in action.parameters]
        allowed = self._allowed[str(action.name)]

        bindings = [{}]
        for atom in _join_order(action, facts):
            bindings = [
                extended
                for binding in bindings
                for fact in facts.matching(atom, binding)
                if (extended := _match(atom, fact, binding, allowed)) is not None
            ]

        candidates = []
        for binding in bindings:
            free = [name for name in parameters if name not in binding]
            for values in product(*[allowed[name] for name in free]):
                complete = {**binding, **dict(zip(free, values))}
                candidates.append(tuple(complete[name] for name in parameters))
        return [
            tuple(self._objects[name] for name in names) for names in sorted(candidates)
        ]

    def is_applicable(self, state: State, action: Action) -> bool:
        """Check if a ground action applies in a state."""
        return is_applicable(state, action)

    def progress(self, state: State, action: Action) -> State:
        """Apply a ground action to a state."""
        return progress(state, action)

    def is_goal(self, state: State) -> bool:
        """Check if a state satisfies the problem's goal."""
        return satisfies(state, self.problem.goal)

    def replay(self, plan: Union[Plan, Sequence[Action]]) -> ReplayResult:
        """Replay a plan from the initial state, stopping at the first failure.

        An invalid step is reported in the result rather than raised.
        """
        steps = (
            plan.actions
            if isinstance(plan, Plan)
            else [(action.name, action.parameters) for action in plan]
        )

        state = self.initial_state
        states = [state]
        for index, (name, objects) in enumerate(steps):
            try:
                state = self.progress(state, self.ground(name, *objects))
            except PDDLLogicError as error:
                reason = f"{_step_text(name, objects)}: {error.message}"
                return ReplayResult(tuple(states), index, reason, False)
            states.append(state)
        return ReplayResult(tuple(states), None, None, self.is_goal(state))


class _FactIndex:
    """The facts of a state, found by predicate or by an argument's position."""

    def __init__(self, state: State):
        self.by_predicate: dict[str, list[Predicate]] = {}
        self._by_argument: dict[tuple, list[Predicate]] = {}
        for fact in state:
            predicate = str(fact.name)
            self.by_predicate.setdefault(predicate, []).append(fact)
            for position, term in enumerate(fact.terms):
                key = (predicate, position, str(term.name))
                self._by_argument.setdefault(key, []).append(fact)

    def matching(self, atom: Predicate, binding: dict) -> list[Predicate]:
        """List the fewest facts that could match the atom, given a binding."""
        predicate = str(atom.name)
        candidates = self.by_predicate.get(predicate, [])
        for position, term in enumerate(atom.terms):
            name = str(term.name)
            value = binding.get(name) if isinstance(term, Variable) else name
            if value is not None:
                found = self._by_argument.get((predicate, position, value), [])
                if len(found) < len(candidates):
                    candidates = found
        return candidates


def _variables(atom: Predicate) -> set[str]:
    return {str(term.name) for term in atom.terms if isinstance(term, Variable)}


def _join_order(action: Action, facts: _FactIndex) -> list[Predicate]:
    """Order positive preconditions so each one shares parameters with earlier ones."""
    precondition = get_precondition(action)
    if precondition is None:
        return []
    conjuncts = getattr(precondition, "operands", (precondition,))
    remaining = [atom for atom in conjuncts if isinstance(atom, Predicate)]

    def cost(atom: Predicate, bound: set[str]) -> tuple:
        variables = _variables(atom)
        unbound = len(variables - bound)
        count = len(facts.by_predicate.get(str(atom.name), ()))
        if unbound < len(variables) or not variables:
            return (0, unbound, count)
        return (1, count, unbound)

    ordered: list[Predicate] = []
    bound: set[str] = set()
    while remaining:
        atom = min(remaining, key=lambda candidate: cost(candidate, bound))
        remaining.remove(atom)
        ordered.append(atom)
        bound |= _variables(atom)
    return ordered


def _match(
    atom: Predicate, fact: Predicate, binding: dict, allowed: dict
) -> Optional[dict]:
    """Extend a binding so the atom equals the fact, or return None if it can't."""
    if len(atom.terms) != len(fact.terms):
        return None

    extended = dict(binding)
    for term, value in zip(atom.terms, fact.terms):
        name = str(value.name)
        if isinstance(term, Variable):
            parameter = str(term.name)
            if name not in allowed[parameter]:
                return None
            if extended.setdefault(parameter, name) != name:
                return None
        elif str(term.name) != name:
            return None
    return extended


def _step_text(name: str, objects: Sequence) -> str:
    names = [str(getattr(obj, "name", obj)) for obj in objects]
    return f"({' '.join([str(name), *names])})"


def _merge_objects(*groups: Iterable[Constant]) -> dict[str, Constant]:
    merged: dict[str, Constant] = {}
    for obj in (obj for group in groups for obj in group):
        name = str(obj.name)
        if name in merged and merged[name].type_tag != obj.type_tag:
            raise PDDLLogicError(
                f"Object {name} has two types: "
                f"{merged[name].type_tag} and {obj.type_tag}"
            )
        merged[name] = obj
    return merged


def _initial_state(init: Iterable) -> frozenset:
    """Keep the true atoms, since anything not listed as true is false."""
    atoms = set()
    for fact in init:
        if isinstance(fact, Predicate):
            atoms.add(fact)
        elif not (isinstance(fact, Not) and isinstance(fact.argument, Predicate)):
            raise NotImplementedError(f"Unsupported initial state entry: {fact}")
    return frozenset(atoms)
