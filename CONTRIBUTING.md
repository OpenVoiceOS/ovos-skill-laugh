# Contributing

Contributions are welcome. Please open an issue before submitting a pull request for significant changes.

## Setup

```bash
pip install -e ".[test]"
```

## Running Tests

```bash
python -m pytest test/
```

With coverage:

```bash
python -m pytest test/ --cov=ovos_skill_laugh --cov-report=term-missing
```

## Branches

- `dev` — active development, open PRs here
- `master` — stable releases only

## Commit Style

This project uses [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` new functionality
- `fix:` bug fixes
- `chore:` maintenance (deps, CI, etc.)
- `docs:` documentation only

## Pull Requests

- Target the `dev` branch
- Include tests for new behavior
- Keep PRs focused — one concern per PR
