
.PHONY: test test-cov test-watch lint format install-dev clean help

# Default target
help:
	@echo "Available commands:"
	@echo "  test        - Run all tests"
	@echo "  test-cov    - Run tests with coverage report"
	@echo "  test-watch  - Run tests in watch mode"
	@echo "  lint        - Run linting checks"
	@echo "  format      - Format code with black and isort"
	@echo "  install-dev - Install development dependencies"
	@echo "  clean       - Clean test artifacts"

# Install development dependencies
install-dev:
	pip install -r requirements.txt
	pip install -r requirements-test.txt
	pip install black isort flake8 bandit safety

# Run tests
test:
	pytest -v

# Run tests with coverage
test-cov:
	pytest --cov=backend --cov-report=html --cov-report=term-missing -v

# Run tests in watch mode
test-watch:
	pytest-watch -- -v

# Lint code
lint:
	flake8 .
	bandit -r . -x tests/
	safety check

# Format code
format:
	black .
	isort .

# Clean test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf *.xml
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

# Run specific test file
test-file:
	pytest $(FILE) -v

# Run tests matching pattern
test-match:
	pytest -k $(PATTERN) -v
