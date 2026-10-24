.PHONY: install run test lint format typecheck check golden

install: ## Install Python + Node tooling
	uv sync
	npm install

run: ## Run the API locally with auto-reload
	uv run uvicorn --factory pnr_convertor.main:create_app --reload

test: ## Run the test suite with coverage
	uv run pytest --cov

golden: ## Regenerate golden expected outputs (review the diff!)
	UPDATE_GOLDEN=1 uv run pytest tests/golden

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
