# pddl-utils

Library of miscellaneous utilies to work with PDDL (both in Python and on the command line).

## Installation

```bash
pip install pddl-utils
```

## Usage

### Python

```python
import pddlutils as pu

# Bind a domain and problem together, from files or parsed `pddl` objects.
task = pu.Task('domain.pddl', 'problem.pddl')

# A state is the set of ground atoms that are true.
state = task.initial_state

# List ground actions and atoms, sorted by name and then object names.
actions = task.applicable_actions(state)
atoms = task.ground_atoms()

# Ground an action by name. Wrong types, arity or names raise PDDLLogicError.
move = task.ground('move', 'person1', 'loc1', 'loc2')

# Check applicability and progress the state.
if task.is_applicable(state, move):
    state = task.progress(state, move)

task.is_goal(state)

# Replay a `pddl` Plan or a list of ground actions. Invalid steps are reported
# in the result instead of being raised.
result = task.replay([move])
result.states          # States visited, starting with the initial state
result.succeeded       # Whether every step applied
result.failed_step     # Index of the first failing step, or None
result.failure_reason  # Why that step failed, or None
result.goal_reached    # Whether the plan succeeded and reached the goal
```

Grounding also works without a `Task`, given the domain for its type hierarchy:

```python
domain, problem = pu.load('domain.pddl', 'problem.pddl')

a = domain.action['move']
p1 = domain.constant['person1']
l1 = problem.object['loc1']
l2 = problem.object['loc2']

ag = pu.ground(a, p1, l1, l2, domain=domain)
```

### Supported PDDL

States and actions support `:strips`, `:typing`, `:negative-preconditions` and `:equality`. If an add and a delete effect name the same atom, the atom ends up true. `Task` raises `NotImplementedError` for a domain outside this fragment.

## Planned Usage

### CLI

Progress the initial state through a plan, and create a new problem file with the final state reached.

```bash
$ planutils progress --domain domain.pddl --problem problem.pddl --plan plan.ipc --output new-problem.pddl
```
