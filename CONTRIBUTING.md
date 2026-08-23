# Contributing to AuthForge

## Setup

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate  | Linux: source .venv/bin/activate
pip install -r requirements.txt
pip install -e ".[dev]"
pre-commit install
cp .env.example .env
# edit .env with DATABASE_URL, JWT_SECRET_KEY (>=32 chars), REDIS_HOST
alembic upgrade head
python scripts/seed_roles.py
```

## Workflow

1. Create branch: `git checkout -b feat/your-feature`
2. Code + add tests in `tests/`
3. Lint & format: `make lint && make format` (or `ruff check .`)
4. Test: `pytest -v` (requires Postgres+Redis or USE_FAKE_REDIS=1)
5. Commit: `git commit -m "feat: ..."` (conventional commits)
6. Push & open PR — CI must pass (ruff, black, pytest, migrations)

## Code Style

- Python 3.11, line length 100, `ruff` + `black` enforced in CI.
- Use `app/modules/<domain>/{models,schemas,repository,service,routes}.py` pattern.
- Add `field_validator` for config, `Index` for DB queries, pagination for list endpoints.

## Security

- Never commit `.env` — only `.env.example`.
- Rotate `JWT_SECRET_KEY` if leaked; min 32 chars.
- Hash passwords via `app/core/security.py`; never log tokens.

## Testing

```bash
USE_FAKE_REDIS=1 pytest --cov=app
```
