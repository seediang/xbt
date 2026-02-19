---
kind: fixed
component: devcontainer
summary: Use dependency group sync for uv in postStartCommand
---

Updated the devcontainer post-start setup to run `uv sync --group dev` instead of
`uv sync --extra dev`.

The project defines development dependencies under `[dependency-groups]` in
`pyproject.toml`, so using `--group` prevents startup failures in the dev container.
