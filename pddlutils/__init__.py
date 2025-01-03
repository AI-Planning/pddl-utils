
from pddl import parse_domain, parse_problem

from pddlutils.grounding import ground

__all__ = ['load', 'ground']

def load(_domain, _problem):

    # If string, load from file. Otherwise, assume it's already loaded
    if isinstance(_domain, str):
        domain = parse_domain(_domain)
    else:
        domain = _domain

    if isinstance(_problem, str):
        problem = parse_problem(_problem)
    else:
        problem = _problem

    domain.action = {}
    for action in domain.actions:
        domain.action[action.name] = action

    domain.predicate = {}
    for predicate in domain.predicates:
        domain.predicate[predicate.name] = predicate

    domain.constant = {}
    for constant in domain.constants:
        domain.constant[constant.name] = constant

    problem.object = {}
    for obj in problem.objects:
        problem.object[obj.name] = obj

    return (domain, problem)
