.PHONY: install test lint format type-check clean dev-install run

# Install production dependencies
install:
	uv sync

# Install development dependencies  
dev-install:
	uv sync --dev

# Run tests
test:
	uv run pytest

# Run tests with coverage
test-cov:
	uv run pytest --cov=app --cov-report=html --cov-report=term

# Lint code
lint:
	uv run ruff check .

# Format code
format:
	uv run ruff format .

# Type check
type-check:
	uv run mypy app

# Run all checks
check: lint type-check test

# Clean up
clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .mypy_cache
	rm -rf __pycache__
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Run the MCP server
run:
	uv run -m interfaces.mcp.server

# Development mode (with auto-reload)
dev:
	uv run -m interfaces.mcp.server
