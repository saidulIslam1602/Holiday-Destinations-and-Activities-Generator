.PHONY: help install dev-install test lint format type-check clean run docker-build docker-run docker-compose-up docker-compose-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install          Install production dependencies"
	@echo "  dev-install      Install development dependencies"
	@echo "  test             Run tests"
	@echo "  test-cov         Run tests with coverage"
	@echo "  lint             Run linting (flake8)"
	@echo "  format           Format code (black + isort)"
	@echo "  type-check       Run type checking (mypy)"
	@echo "  clean            Clean cache and build files"
	@echo "  run              Run the application"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-compose-up    Start with Docker Compose"
	@echo "  docker-compose-down  Stop Docker Compose"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e ".[dev]"
	pre-commit install

# Testing
test:
	pytest

test-cov:
	pytest --cov=src --cov-report=html --cov-report=term-missing

# Code quality
lint:
	flake8 src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Development
run:
	streamlit run app.py

# Docker
docker-build:
	docker build -t holiday-destinations-generator .

docker-run:
	docker run -p 8501:8501 --env-file .env holiday-destinations-generator

docker-compose-up:
	docker-compose up -d

docker-compose-down:
	docker-compose down

# All quality checks
check: lint type-check test

# Setup development environment
setup-dev: dev-install
	cp env.example .env
	@echo "Please edit .env with your configuration" 