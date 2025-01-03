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

# Extended wrapper of the pddl library.
domain, problem = pu.load('domain.pddl', 'problem.pddl')

# Alternatively, if you have a pddl dom,prob pair, you can wrap it using...
# domain, problem = pu.load(dom, prob)

# Set of (lifted) fluents and actions
domain.predicates
domain.actions

# Access a particular action or fluent or constant/object
a = domain.action['move']
f = domain.predicate['connected']

p1 = domain.constant['person1']
l1 = problem.object['loc1']
l2 = problem.object['loc2']

# Ground a predicate
f = pu.ground(f, l1, l2)

# Ground an action
ag = pu.ground(a, p1, l1, l2)
```

## Planned Usage

### Python

```python
import pddlutils as pu

# Extended wrapper of the pddl library.
domain, problem = pu.load('domain.pddl', 'problem.pddl')

# Alternatively, if you have a pddl dom,prob pair, you can wrap it using...
# domain, problem = pu.load(dom, prob)

# Set of (lifted) fluents and actions
domain.predicates
domain.actions

# Access a particular action or fluent or constant/object
a = domain.action['move']
f = domain.predicate['connected']

p1 = domain.constant['person1']
l1 = problem.object['loc1']
l2 = problem.object['loc2']

# Ground a predicate
f = pu.ground(f, l1, l2)

# Ground an action
ag = pu.ground(a, p1, l1, l2)

# Ground an entire domain (actions and fluents replaced with type-specific ground versions)
gdom, gprob = pu.ground(domain, problem)

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

### CLI

Progress the initial state through a plan, and create a new problem file with the final state reached.

```bash
$ planutils progress --domain domain.pddl --problem problem.pddl --plan plan.ipc --output new-problem.pddl
```
