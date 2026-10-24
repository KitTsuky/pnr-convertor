.PHONY: install run test lint format typecheck check golden airlines

install: ## Install Python + Node tooling
	uv sync
	npm install

run: ## Run the API locally with auto-reload
	uv run uvicorn --factory pnr_convertor.main:create_app --reload

test: ## Run the test suite with coverage
	uv run pytest --cov

golden: ## Regenerate golden expected outputs (review the diff!)
	UPDATE_GOLDEN=1 uv run pytest tests/golden

airlines: ## Rebuild bundled airline names from OpenFlights (review the diff!)
	curl -fsSL -o /tmp/airlines.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat
	uv run python scripts/build_airlines.py /tmp/airlines.dat src/pnr_convertor/data/airlines.json

lint: ## Lint + format checks (no changes)
	uv run ruff check .
	uv run ruff format --check .
	npx prettier --check .

format: ## Auto-fix lint issues and format everything
	uv run ruff check --fix .
	uv run ruff format .
	npx prettier --write .

typecheck: ## Strict static type checking
	uv run mypy

check: lint typecheck test ## Everything CI runs
