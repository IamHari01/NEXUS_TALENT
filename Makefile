# --- Variables ---
DC=docker-compose
BACKEND_DIR=backend
FRONTEND_DIR=frontend

# --- Build & Run ---
.PHONY: up
up: ## Start all services in detached mode
	$(DC) up --build -d

.PHONY: down
down: ## Stop and remove all containers
	$(DC) down

.PHONY: restart
restart: down up ## Full restart of the stack

# --- Initialization & Maintenance ---
.PHONY: init-db
init-db: ## Initialize Weaviate schema and classes
	docker-compose exec api python -m app.scripts.init_weaviate

.PHONY: clean-cache
clean-cache: ## Flush all data from Redis
	docker-compose exec redis redis-cli flushall

# --- Development & Debugging ---
.PHONY: logs
logs: ## Stream logs from the API and Agents
	$(DC) logs -f api

.PHONY: test
test: ## Run backend unit tests
	docker-compose exec api pytest

.PHONY: signoz
signoz: ## Open the SigNoz dashboard (Linux/Mac)
	open http://localhost:3301 || xdg-open http://localhost:3301

# --- Help ---
.PHONY: help
help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'