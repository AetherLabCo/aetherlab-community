# Contributing to the AetherLab Python SDK

Thanks for your interest in contributing!

## Reporting issues

If you find a bug or have a feature request:

1. Check the [issue tracker](https://github.com/AetherLabCo/aetherlab-community/issues) for existing reports.
2. Open a new issue with a clear title, steps to reproduce (for bugs),
   expected vs. actual behavior, and your environment (OS, Python version,
   SDK version).

## Development setup

```bash
git clone https://github.com/AetherLabCo/aetherlab-community.git
cd aetherlab-community
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Running checks

```bash
ruff check src tests examples   # lint
mypy                            # type-check (configured in pyproject.toml)
pytest                          # unit tests (all HTTP is mocked)
```

The live smoke tests are skipped unless you export both `AETHERLAB_API_KEY`
and `AETHERLAB_BASE_URL`:

```bash
AETHERLAB_API_KEY=... AETHERLAB_BASE_URL=... pytest tests/test_live_smoke.py
```

Never commit API keys, and never hardcode them in tests or examples.

## Submitting pull requests

1. Fork the repository and create a branch from `main`.
2. Make your changes, including tests for new behavior.
3. Make sure `ruff`, `mypy`, and `pytest` all pass.
4. Use conventional commit messages (e.g. `fix(sdk): handle empty rationale`).
5. Open a pull request describing the change and referencing related issues.

## Questions

Open an issue, or email support@aetherlab.co.
