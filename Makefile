# FDA Search v2 - Development Commands

.PHONY: help setup dev build start stop restart rebuild clean test lint format logs status

help: ## Show this help message
	@echo "FDA Search v2 - Available Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Install all dependencies
	@echo "🔧 Setting up FDA Search v2..."
	cd frontend && npm install
	cd backend && pip install -r requirements.txt
	@echo "✅ Setup complete!"

dev: ## Start development servers
	@echo "🚀 Starting development servers..."
	npm run dev

build: ## Build for production
	@echo "🏗️ Building for production..."
	cd frontend && npm run build
	@echo "✅ Build complete!"

start: ## Start with Docker
	@echo "🐳 Starting with Docker..."
	docker-compose up -d
	@echo "✅ Application running at http://localhost:3000"

stop: ## Stop Docker containers
	@echo "🛑 Stopping containers..."
	docker-compose down

restart: ## Restart Docker containers (quick)
	@echo "🔄 Restarting containers..."
	docker-compose restart
	@echo "✅ Containers restarted!"

rebuild: ## Rebuild and restart containers (with code changes)
	@echo "🔨 Rebuilding containers..."
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ Containers rebuilt and running!"

clean: ## Clean all build artifacts
	@echo "🧹 Cleaning..."
	cd frontend && rm -rf dist node_modules
	cd backend && rm -rf __pycache__ *.pyc
	docker-compose down -v
	@echo "✅ Clean complete!"

test: ## Run tests
	@echo "🧪 Running tests..."
	cd frontend && npm run test
	cd backend && python -m pytest

lint: ## Lint code
	@echo "🔍 Linting..."
	cd frontend && npm run lint

format: ## Format code
	@echo "✨ Formatting..."
	cd frontend && npm run format
	cd backend && python -m black .

logs: ## Show Docker logs
	docker-compose logs -f

status: ## Show running containers
	docker-compose ps

# Quick commands for your workflow
antipsychotics: start ## Start app and open batch query for antipsychotics
	@echo "🧠 Ready for antipsychotic drug analysis!"
	@echo "👉 Open http://localhost:3000/batch"
	@echo "👉 Click 'Antipsychotics (27)' preset"