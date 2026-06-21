# Contributing to WhiteCapData-Dev

Thanks for your interest! This server stays small, focused, and **safe by default** — contributions that preserve those properties merge easiest.

## Getting set up

```bash
git clone https://github.com/Michael-WhiteCapData/WhiteCapData-Dev
cd WhiteCapData-Dev
uv pip install -e ".[dev]"
```

## Before opening a PR

- `ruff check .` passes (`ruff check --fix .` to autofix).
- `pytest` passes. The suite uses fakes/mocks for the Kubernetes API — **no cluster required**.
- New behavior comes with a test.
- Any new **mutating** tool must go through `KubeClient._guard()` (read-only + namespace allowlist) and have a test proving it's blocked when it should be.

## Architecture

- `config.py` — env-driven config + the namespace allowlist logic.
- `format.py` — pure mappers from Kubernetes objects to JSON-able dicts (easy to test).
- `kube.py` — the API facade; reads call mappers, mutations are guarded.
- `server.py` — the MCP tool layer (thin; delegates to `KubeClient`).

## Reporting bugs

Open an issue with what you ran, expected vs. actual, and your `server_info` output.

## Code of conduct

Be decent, assume good faith, keep it constructive.
