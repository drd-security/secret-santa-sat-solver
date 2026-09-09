# Secret Santa SAT Solver

Python implementation of a constrained **Secret Santa assignment problem** encoded as propositional logic and solved with a SAT solver.

## Constraints encoded

The model enforces that:

- every participant gives exactly one gift;
- every participant receives exactly one gift;
- nobody is assigned to themselves;
- members of the same family cannot be paired;
- reciprocal two-person exchanges are forbidden;
- cycles up to a configurable length can be forbidden;
- all satisfying assignments can be enumerated incrementally.

## Technical approach

Each possible directed assignment `giver -> receiver` is represented by a Boolean variable. The project generates CNF clauses and uses **PySAT** for satisfiability/model enumeration, then decodes each model back into human-readable assignments.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Example

```bash
python examples/run_example.py
```

The included CSV is synthetic portfolio data. The original course datasets are not redistributed here.

## Repository structure

```text
src/secret_santa.py       SAT encoding and model decoding
examples/                 synthetic input and demonstration script
requirements.txt          Python dependencies
```

## Academic context

Logic/SAT university project, academic year **2024-2025**. A reliable team-size/task-split record was not preserved in the archive, so this portfolio copy does not make individual-contribution claims beyond the surviving source attribution.

See [NOTICE.md](NOTICE.md) before public release.
