# Project instructions

## Environment
- Use Pixi for project commands and dependency management.
- Commit dependency changes together with pixi.lock.
- Declare dependencies in project configuration; do not rely on manual installations.

## Code structure
- Keep functions, methods, and files short and focused on a clear responsibility.
- Split complex logic into meaningful helper functions.
- Use blank lines to separate logical steps inside functions and methods.
- Use descriptive names and explicit inputs and outputs.
- Keep related code together and avoid unnecessary abstractions.
- Change the smallest reasonable set of files needed for the task.
- Avoid unrelated refactoring, renaming, and formatting changes.

## Code quality
- Ruff settings in pyproject.toml define linting and formatting.
- Run `pixi run lint-fix` and `pixi run format` after Python changes.
- Inspect automatic changes for unintended effects.
- Run `pixi run check` before completing a task.
- Run relevant tests when changing behavior.
- Report checks that failed or could not be run.
- Do not weaken lint rules or add blanket suppressions to pass checks.
- Keep unrelated formatting changes out of focused PRs.
## Research code
- Read docs/research.md before changing data preparation, training,
  evaluation, or experiment reporting.
- Document tensor shapes, units, and non-obvious assumptions.
- Keep training and evaluation logic separate.
- Treat raw data as immutable; write derived data separately.
- Fit learned preprocessing on training data only.
- Preserve group boundaries when splitting related samples,
  such as multiple samples from the same patient.
- Use validation data for model selection; do not tune on test results.
- Document changes to splits, preprocessing, metrics, and evaluation protocols.
- Keep experiment settings in configuration rather than hardcoding them.
- Record the actual code revision, uncommitted changes, resolved configuration,
  seeds, data version/split, and environment reference for reported runs.
- Compare against a documented baseline; disclose differences in the
  evaluation protocol or compute budget.
- Report the number of runs/seeds and variability when available.
  Label single-run results accordingly.
- Distinguish expected benefits from measured improvements.
- Never invent metrics, run completion, citations, or artifact locations.
- Preserve failed and inconclusive results that inform research decisions.
- Use small smoke tests before expensive runs and follow documented
  scheduler requirements and compute budgets.
- Reference relevant papers and document deviations from their methods.

## Documentation
- Explain what changed, why, and how it was validated when completing a task.
- Record meaningful changes and decisions in docs/decisions.md.
- Keep entries concise: context, change or decision, rationale, and relevant consequences.
- Update existing documentation before creating additional files.
- Keep setup instructions and reproducibility commands aligned with the implementation.
- Explain non-obvious configuration settings beside their definitions.
- Update comments and documentation when changing the behavior they describe.

## Dependencies
- Keep every directly declared dependency documented in docs/dependencies.md,
  including runtime, development, and build dependencies.
- Use the columns: Package, Purpose, Alternatives.
- Briefly explain why this project needs each dependency.
- List potential alternative packages by name only; use "None" where appropriate.
- Update this list when adding, removing, or replacing dependencies.
- Keep exact resolved versions and transitive dependencies in pixi.lock;
  do not duplicate that generated information in documentation.
- Reuse existing dependencies where practical and justify new additions.

## Pull requests
- Use the appropriate template from .github/PULL_REQUEST_TEMPLATE/.
- Keep each PR focused on a coherent change.
- Summarize the main affected files, relevant decisions, and validation outcomes.
- State limitations, assumptions, and checks that were not performed.