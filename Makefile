.PHONY: install lint format test run migrate seed clean docker-up docker-down

install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

lint:
	ruff check .

format:
	ruff check --fix .
	black .

test:
	pytest -v --cov=app --cov-report=term-missing

test-quick:
	pytest -q

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

migrate:
	alembic upgrade head

migrate-new:
	alembic revision --autogenerate -m "$(msg)"

seed:
	python scripts/seed_roles.py
	python scripts/seed_admin.py

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v

docker-logs:
	docker compose logs -f api

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache .ruff_cache htmlcov .coverage
