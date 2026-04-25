# ================================================================================
# Makefile — AI Learning System
# ================================================================================
# Upotreba: make <target>
# Pokrenite 'make help' za prikaz svih dostupnih komandi.
#
# Varijable koje možete pregaziti:
#   TAG      — Docker image tag (default: latest)
#   ENV      — Okruženje za deploy (default: staging)
#   COMPOSE  — docker compose fajl (default: docker/docker-compose.yml)
# ================================================================================

.DEFAULT_GOAL := help

# ── Konfiguracija ─────────────────────────────────────────────────────────────
TAG    ?= latest
ENV    ?= staging
COMPOSE_DEV  := docker/docker-compose.yml
COMPOSE_PROD := docker/docker-compose.prod.yml
DOCKER_DIR   := docker
BACKEND_DIR  := backend
FRONTEND_DIR := frontend

# Boje za output
BOLD  := \033[1m
GREEN := \033[0;32m
CYAN  := \033[0;36m
NC    := \033[0m

# ── Auto-dokumentacija (parsira ## komentare) ─────────────────────────────────
.PHONY: help
help: ## Prikaži ovu poruku sa svim dostupnim komandama
	@echo ""
	@echo "$(BOLD)AI Learning System — Make komande$(NC)"
	@echo "$(CYAN)══════════════════════════════════════════════$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-22s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(BOLD)Varijable:$(NC)"
	@echo "  TAG=$(TAG)   — image tag (npr: make deploy-prod TAG=v1.2.3)"
	@echo "  ENV=$(ENV)   — okruženje  (npr: make deploy ENV=production)"
	@echo ""

# ── Build ─────────────────────────────────────────────────────────────────────
.PHONY: build
build: ## Izgradi sve Docker images lokalno
	@echo "$(BOLD)Izgradnja Docker images...$(NC)"
	docker build -t ai-learning-backend:$(TAG) ./$(BACKEND_DIR)
	docker build -t ai-learning-frontend:$(TAG) ./$(FRONTEND_DIR)
	@echo "$(GREEN)✅ Build završen!$(NC)"

.PHONY: build-prod
build-prod: ## Izgradi produkcijske Docker images (Dockerfile.prod)
	@echo "$(BOLD)Izgradnja produkcijskih Docker images...$(NC)"
	docker build -f $(BACKEND_DIR)/Dockerfile.prod \
		-t ai-learning-backend:$(TAG)-prod ./$(BACKEND_DIR)
	docker build -t ai-learning-frontend:$(TAG)-prod ./$(FRONTEND_DIR)
	@echo "$(GREEN)✅ Produkcijski build završen!$(NC)"

.PHONY: frontend-build
frontend-build: ## Izgradi frontend (Node.js via Docker — bez lokalne instalacije)
	@echo "$(BOLD)Izgradnja frontenda...$(NC)"
	docker run --rm \
		-v "$(PWD)/$(FRONTEND_DIR)":/app \
		-w /app \
		node:20-alpine \
		sh -c "npm ci && npm run build"
	@echo "$(GREEN)✅ Frontend izgrađen u frontend/dist/$(NC)"

# ── Testovi ───────────────────────────────────────────────────────────────────
.PHONY: test
test: test-backend test-frontend ## Pokreni sve testove (backend + frontend)
	@echo "$(GREEN)✅ Svi testovi završeni!$(NC)"

.PHONY: test-backend
test-backend: ## Pokreni backend testove (pytest)
	@echo "$(BOLD)Backend testovi...$(NC)"
	cd $(BACKEND_DIR) && \
		DATABASE_URL=sqlite:///:memory: \
		REDIS_URL=redis://localhost:6379/0 \
		SECRET_KEY=test-secret-key-32-chars-minimum!! \
		ENVIRONMENT=testing \
		python -m pytest app/tests/ -v --tb=short --no-header -q

.PHONY: test-backend-coverage
test-backend-coverage: ## Backend testovi sa coverage izvještajem
	@echo "$(BOLD)Backend testovi sa coverage...$(NC)"
	cd $(BACKEND_DIR) && \
		DATABASE_URL=sqlite:///:memory: \
		REDIS_URL=redis://localhost:6379/0 \
		SECRET_KEY=test-secret-key-32-chars-minimum!! \
		ENVIRONMENT=testing \
		python -m pytest app/tests/ \
			--cov=app \
			--cov-report=term-missing \
			--cov-report=html:htmlcov \
			--cov-fail-under=60 \
			-q
	@echo "$(GREEN)HTML coverage: backend/htmlcov/index.html$(NC)"

.PHONY: test-frontend
test-frontend: ## Pokreni frontend testove (ako postoje)
	@echo "$(BOLD)Frontend provjere...$(NC)"
	cd $(FRONTEND_DIR) && npx tsc --noEmit
	@echo "$(GREEN)✅ TypeScript provjera prošla!$(NC)"

# ── Linting ───────────────────────────────────────────────────────────────────
.PHONY: lint
lint: lint-backend lint-frontend ## Pokreni sve lintere

.PHONY: lint-backend
lint-backend: ## Lint Python koda (flake8)
	@echo "$(BOLD)Python lint (flake8)...$(NC)"
	cd $(BACKEND_DIR) && \
		flake8 app \
			--max-line-length=120 \
			--extend-ignore=E203,W503,E501 \
			--exclude=app/db/migrations
	@echo "$(GREEN)✅ Python lint prošao!$(NC)"

.PHONY: lint-frontend
lint-frontend: ## Lint TypeScript/React koda
	@echo "$(BOLD)Frontend lint...$(NC)"
	cd $(FRONTEND_DIR) && npx tsc --noEmit
	@echo "$(GREEN)✅ TypeScript lint prošao!$(NC)"

# ── Lokalni deploy ────────────────────────────────────────────────────────────
.PHONY: deploy-local
deploy-local: ## Lokalni deploy — docker compose up -d --build
	@echo "$(BOLD)Lokalni deploy...$(NC)"
	cd $(DOCKER_DIR) && docker compose up -d --build
	@echo "$(GREEN)✅ Pokrenuto lokalno!$(NC)"
	@echo "  Backend:  http://localhost:8000"
	@echo "  Frontend: http://localhost:80"
	@echo "  API Docs: http://localhost:8000/docs"
	@echo ""
	@echo "Logovi: make logs"

.PHONY: deploy-local-script
deploy-local-script: ## Lokalni deploy via scripts/deploy.sh (sa health check i rollback)
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh --env local --tag $(TAG)

# ── Remote deploy ─────────────────────────────────────────────────────────────
.PHONY: deploy-staging
deploy-staging: ## Deploy na staging server (potrebni SSH env vars)
	@echo "$(BOLD)Deploy na staging (tag: $(TAG))...$(NC)"
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh --env staging --tag $(TAG)

.PHONY: deploy-prod
deploy-prod: ## Deploy na produkciju — OBAVEZNO koristiti TAG: make deploy-prod TAG=v1.2.3
	@if [ "$(TAG)" = "latest" ]; then \
		echo "$(BOLD)GREŠKA: Za produkciju koristite semantički tag!$(NC)"; \
		echo "Primjer: make deploy-prod TAG=v1.2.3"; \
		exit 1; \
	fi
	@echo "$(BOLD)⚠️  Produkcijski deploy (tag: $(TAG))$(NC)"
	@read -p "Sigurni ste? Deployujete $(TAG) na produkciju. [y/N] " confirm && \
		[ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]
	@chmod +x scripts/deploy.sh
	./scripts/deploy.sh --env production --tag $(TAG)

# ── Up/Down ───────────────────────────────────────────────────────────────────
.PHONY: up
up: ## Pokreni razvojno okruženje (bez rebuilda)
	cd $(DOCKER_DIR) && docker compose up -d

.PHONY: down
down: ## Zaustavi sve kontejnere
	cd $(DOCKER_DIR) && docker compose down

.PHONY: restart
restart: down up ## Restart svih servisa

.PHONY: nginx-reload
nginx-reload: ## Reloaduj nginx konfiguraciju (bez restarta)
	cd $(DOCKER_DIR) && docker compose exec nginx nginx -s reload
	@echo "✅ Nginx konfiguracija reloadovana"

.PHONY: up-prod
up-prod: ## Pokreni produkcijsko okruženje lokalno (docker-compose.prod.yml)
	cd $(DOCKER_DIR) && docker compose -f $(notdir $(COMPOSE_PROD)) up -d

.PHONY: down-prod
down-prod: ## Zaustavi produkcijsko okruženje
	cd $(DOCKER_DIR) && docker compose -f $(notdir $(COMPOSE_PROD)) down

# ── Logovi i status ───────────────────────────────────────────────────────────
.PHONY: logs
logs: ## Prikaži logove svih kontejnera (live)
	cd $(DOCKER_DIR) && docker compose logs -f

.PHONY: logs-app
logs-app: ## Prikaži logove samo backend servisa
	cd $(DOCKER_DIR) && docker compose logs -f app

.PHONY: logs-prod
logs-prod: ## Prikaži logove produkcijskog okruženja
	cd $(DOCKER_DIR) && docker compose -f $(notdir $(COMPOSE_PROD)) logs -f

.PHONY: status
status: ## Prikaži status svih kontejnera i njihovo zdravlje
	@echo "$(BOLD)Status kontejnera:$(NC)"
	cd $(DOCKER_DIR) && docker compose ps
	@echo ""
	@echo "$(BOLD)Korištenje resursa:$(NC)"
	docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" 2>/dev/null || true

.PHONY: health
health: ## Provjeri health check endpoint
	@echo "$(BOLD)Health check...$(NC)"
	@curl -sf http://localhost:8000/health 2>/dev/null && \
		echo "$(GREEN)✅ Backend je zdrav!$(NC)" || \
		echo "$(BOLD)❌ Backend nije dostupan$(NC)"
	@curl -sf http://localhost/health 2>/dev/null && \
		echo "$(GREEN)✅ Nginx je zdrav!$(NC)" || \
		echo "$(BOLD)❌ Nginx nije dostupan$(NC)"

# ── Baza podataka ─────────────────────────────────────────────────────────────
.PHONY: db-migrate
db-migrate: ## Pokreni Alembic migracije baze podataka
	@echo "$(BOLD)Alembic migracije...$(NC)"
	cd $(DOCKER_DIR) && docker compose exec app alembic upgrade head

.PHONY: db-rollback
db-rollback: ## Rollback zadnje migracije
	@echo "$(BOLD)Rollback migracije...$(NC)"
	cd $(DOCKER_DIR) && docker compose exec app alembic downgrade -1

.PHONY: db-shell
db-shell: ## Otvori PostgreSQL shell
	cd $(DOCKER_DIR) && docker compose exec db psql -U $${POSTGRES_USER:-ailearning} -d $${POSTGRES_DB:-ailearning_db}

# ── Shell pristup ─────────────────────────────────────────────────────────────
.PHONY: shell
shell: ## Otvori bash shell u backend kontejneru
	cd $(DOCKER_DIR) && docker compose exec app bash

.PHONY: shell-frontend
shell-frontend: ## Otvori sh shell u frontend kontejneru
	cd $(DOCKER_DIR) && docker compose exec frontend sh

# ── Čišćenje ──────────────────────────────────────────────────────────────────
.PHONY: clean
clean: ## Ukloni zaustavljene kontejnere i dangling images
	@echo "$(BOLD)Čišćenje...$(NC)"
	docker container prune -f
	docker image prune -f
	docker volume prune -f
	@echo "$(GREEN)✅ Čišćenje završeno!$(NC)"

.PHONY: clean-all
clean-all: down clean ## Zaustavi sve i duboko čišćenje (volumes i networks)
	@echo "$(BOLD)Duboko čišćenje (volumes + networks)...$(NC)"
	cd $(DOCKER_DIR) && docker compose down -v --remove-orphans
	docker system prune -f
	@echo "$(GREEN)✅ Duboko čišćenje završeno!$(NC)"

.PHONY: clean-frontend
clean-frontend: ## Ukloni frontend build artefakte
	rm -rf $(FRONTEND_DIR)/dist $(FRONTEND_DIR)/node_modules/.cache
	@echo "$(GREEN)✅ Frontend artefakti uklonjeni!$(NC)"

# ── CI/CD simulacija ──────────────────────────────────────────────────────────
.PHONY: ci
ci: lint test build ## Simuliraj CI pipeline lokalno (lint + test + build)
	@echo "$(GREEN)$(BOLD)✅ Lokalni CI prolazi!$(NC)"

.PHONY: ci-full
ci-full: lint test-backend-coverage build frontend-build ## Puni CI sa coverage izvještajem
	@echo "$(GREEN)$(BOLD)✅ Puni lokalni CI prolazi!$(NC)"

# ── Git pomocne komande ───────────────────────────────────────────────────────
.PHONY: tag-release
tag-release: ## Kreiraj release tag (make tag-release TAG=v1.2.3)
	@if [ "$(TAG)" = "latest" ]; then \
		echo "GREŠKA: Navedite TAG, npr: make tag-release TAG=v1.2.3"; \
		exit 1; \
	fi
	@echo "$(BOLD)Kreiranje taga $(TAG)...$(NC)"
	git tag -a $(TAG) -m "Release $(TAG)"
	git push origin $(TAG)
	@echo "$(GREEN)✅ Tag $(TAG) pushovan! CD workflow će se automatski pokrenuti.$(NC)"

.PHONY: release
release: ## Interaktivni release wizard (lint + test + tag + push)
	@echo "$(BOLD)Release wizard$(NC)"
	@read -p "Nova verzija (npr: v1.2.3): " ver && \
		$(MAKE) ci && \
		git tag -a "$$ver" -m "Release $$ver" && \
		git push origin main "$$ver" && \
		echo "$(GREEN)$(BOLD)🚀 Release $$ver pokrenut!$(NC)"

# ── Informativne komande ──────────────────────────────────────────────────────
.PHONY: version
version: ## Prikaži trenutnu verziju projekta
	@echo "$(BOLD)Git verzija:$(NC)"
	@git describe --tags --always --dirty 2>/dev/null || git rev-parse --short HEAD
	@echo "$(BOLD)Docker images:$(NC)"
	@docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedSince}}" \
		| grep "ai-learning" || echo "  (nema lokalnih images)"

.PHONY: env-check
env-check: ## Provjeri da li su sve potrebne env varijable postavljene
	@echo "$(BOLD)Provjera environment varijabli...$(NC)"
	@[ -f $(DOCKER_DIR)/.env ] && \
		echo "$(GREEN)✅ docker/.env postoji$(NC)" || \
		echo "$(BOLD)⚠️  docker/.env ne postoji — kopirajte iz docker/.env.example$(NC)"
	@echo ""
	@echo "$(BOLD)Staging SSH:$(NC)"
	@for v in STAGING_SSH_HOST STAGING_SSH_USER STAGING_SSH_KEY STAGING_APP_DIR; do \
		[ -n "$${!v:-}" ] && \
			echo "  $(GREEN)✅ $$v$(NC)" || \
			echo "  ❌ $$v nije postavljen"; \
	done
	@echo ""
	@echo "$(BOLD)Production SSH:$(NC)"
	@for v in PRODUCTION_SSH_HOST PRODUCTION_SSH_USER PRODUCTION_SSH_KEY PRODUCTION_APP_DIR; do \
		[ -n "$${!v:-}" ] && \
			echo "  $(GREEN)✅ $$v$(NC)" || \
			echo "  ❌ $$v nije postavljen"; \
	done
	@echo ""
	@echo "$(BOLD)Docker Hub:$(NC)"
	@for v in DOCKER_HUB_USERNAME DOCKER_HUB_TOKEN; do \
		[ -n "$${!v:-}" ] && \
			echo "  $(GREEN)✅ $$v$(NC)" || \
			echo "  ⚠️  $$v nije postavljen (opciono)"; \
	done

.PHONY: docs
docs: ## Otvori dokumentaciju u browseru (ako je xdg-open dostupan)
	@xdg-open CI_CD_STRATEGIJA.md 2>/dev/null || \
		cat CI_CD_STRATEGIJA.md | head -50
