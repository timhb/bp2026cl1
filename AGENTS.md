# Agent instructions

## Rule 0

Verbosity is the enemy of quality. Conciseness and brevity are king. This project is for busy
humans who want to grasp the most important aspects of your work in as little time as possible.
Generally, refrain from creating or growing `.md` files.

## Rules

[docs/rules.md](docs/rules.md) holds the project's current conventions. Follow it; when a
convention changes, edit it in place instead of appending.

## Code

- Use Pixi for commands and dependencies; commit `pixi.lock` with dependency changes.
- Code lives in the `bp26` package (`src/bp26/`).
- Small, focused functions and files; descriptive names; no needless abstractions.
- Change the fewest files needed; no unrelated refactoring or formatting.
- Before finishing: `pixi run lint-fix`, `pixi run format`, `pixi run check`, relevant tests.
  Never weaken lint rules to pass. Report checks that failed or were not run.

## Research

- Raw data is immutable and never committed; write derived data separately.
- Fit preprocessing on training data only; split by patient/case, not by sample.
- Select models on validation data, never on test results.
- Settings go in `configs/`, not hardcoded. Smoke-test before expensive runs.
- Record code revision, config, seeds, data split and hardware for reported runs
  in [docs/experiments.md](docs/experiments.md).
- Never invent metrics, results, citations or file locations. Label single-run results as such.

## Pull requests

Use the template in `.github/`; one coherent change per PR. State what changed, why, and how
it was validated.
