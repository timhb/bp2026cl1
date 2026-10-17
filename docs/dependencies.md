## Pixi

- **Purpose:** Manage project dependencies, environments, and shared task commands. Use `pixi install --locked` for setup and `pixi run <task>` for project commands; see the [Pixi guide](guides/pixi.md).
- **Why Pixi over Conda:** For our eight-person team, Pixi brings dependency declarations, automatic lockfile management, and named tasks into one repository-based workflow. Dependency changes are recorded in configuration and the lockfile, making them reviewable in PRs. Pixi still uses the Conda ecosystem. Conda also supports reproducible environments and lockfiles, we chose Pixi for its integrated workflow. See [Pixi's comparison](https://pixi.prefix.dev/latest/switching_from/conda/) and [Conda's lockfile support](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html#building-identical-conda-environments).
- **Alternatives:** Conda, Mamba, uv.


## Ruff

- **Purpose:** Python linting, import sorting, and formatting; configured in `pyproject.toml`.
- **Usage:** Run `pixi run lint-fix` and `pixi run format`, review edits, then run `pixi run --locked check`.
- **Alternatives:** Flake8, isort, Black.