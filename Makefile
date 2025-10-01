# Cross-Border Tax Consultant - Development Commands

.PHONY: help build up down dev logs clean restart test test-build test-shell test-coverage test-clean

# Default target
help: ## Show this help message
	@echo "Cross-Border Tax Consultant - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Production commands
build: ## Build all Docker images
	docker-compose build

up: ## Start the application in production mode
	docker-compose up -d

down: ## Stop the application
	docker-compose down

logs: ## Show application logs
	docker-compose logs -f

restart: ## Restart the application
	docker-compose restart

# Development commands
dev: ## Start the application in development mode with hot reload
	docker-compose -f docker-compose.dev.yml up --build

dev-down: ## Stop the development application
	docker-compose -f docker-compose.dev.yml down

dev-logs: ## Show development logs
	docker-compose -f docker-compose.dev.yml logs -f

# Utility commands
clean: ## Remove all containers, images, and volumes
	docker-compose down -v --remove-orphans
	docker-compose -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -af

status: ## Show running containers
	docker-compose ps

shell-backend: ## Access backend container shell
	docker-compose exec backend bash

shell-frontend: ## Access frontend container shell
	docker-compose exec frontend sh

# Setup commands
setup: ## Initial setup - copy env file and build
	@echo "For Windows users, please run: setup.bat or setup.ps1"
	@echo "For Unix/Linux/Mac users:"
	@test -f .env || (cp .env.example .env && echo "Created .env file. Please update with your API keys.")
	docker-compose build

# Testing commands
test: ## Run all backend tests in Docker
	docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit

test-build: ## Build test container
	docker-compose -f docker-compose.test.yml build

test-shell: ## Access test container shell for interactive testing
	docker-compose -f docker-compose.test.yml run tests bash

test-coverage: ## Run tests with coverage report
	docker-compose -f docker-compose.test.yml run tests pytest --cov --cov-report=html

test-specific: ## Run specific test (usage: make test-specific TEST=test_parser.py)
	docker-compose -f docker-compose.test.yml run tests python $(TEST)

test-clean: ## Clean test containers and volumes
	docker-compose -f docker-compose.test.yml down -v
	rm -rf test-results

test-logs: ## Show test container logs
	docker-compose -f docker-compose.test.yml logs -f