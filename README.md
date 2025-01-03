# pddl-utils

Library of miscellaneous utilies to work with PDDL (both in Python and on the command line).

## Installation

```bash
pip install pddl-utils
```

## Usage

Coming soon...

## Planned Usage

### Python Usage

```python
import pddlutils as pu

problem = pu.load('domain.pddl', 'problem.pddl')

# Set of (lifted) fluents and actions
problem.fluents
problem.actions

# Ground things (actions and fluents replaced with type-specific ground versions)
problem.ground()

# Easy progression
s0 = problem.init
act = list(problem.actions)[0]
s1 = tl.progress(s0, act)

# Easy action/fluent lookup
act = problem.action('move loc1 loc2')
fluent = problem.fluent('connected loc1 loc2')
assert fluent == problem.fluent('(connected loc1 loc2)')

# parses plans from file, string, or list
plan = problem.parse_plan('plan.ipc')
plan = problem.parse_plan('(move loc1 loc2)\n(move loc2 loc3)')
plan = problem.parse_plan(['move loc1 loc2', 'move loc2 loc3'])
```

### Command Line Usage

Progress the initial state through a plan, and create a new problem file with the final state reached.

```bash
$ planutils progress --domain domain.pddl --problem problem.pddl --plan plan.ipc --output new-problem.pddl
```
