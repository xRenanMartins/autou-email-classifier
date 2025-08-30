# Makefile para Email Classifier
.PHONY: help install dev test build clean docker-up docker-down

# Variáveis
PYTHON = python3
PIP = pip3
NODE = node
NPM = npm
DOCKER = docker
DOCKER_COMPOSE = docker-compose

# Cores para output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Mostra esta ajuda
	@echo "$(GREEN)Email Classifier - Comandos disponíveis:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Instala dependências do projeto
	@echo "$(GREEN)Instalando dependências...$(NC)"
	@cd app/backend && $(PIP) install -r requirements.txt
	@cd app/frontend && $(NPM) install
	@echo "$(GREEN)Dependências instaladas com sucesso!$(NC)"

install-backend: ## Instala apenas dependências do backend
	@echo "$(GREEN)Instalando dependências do backend...$(NC)"
	@cd app/backend && $(PIP) install -r requirements.txt
	@echo "$(GREEN)Backend instalado com sucesso!$(NC)"

install-frontend: ## Instala apenas dependências do frontend
	@echo "$(GREEN)Instalando dependências do frontend...$(NC)"
	@cd app/frontend && $(NPM) install
	@echo "$(GREEN)Frontend instalado com sucesso!$(NC)"

dev: ## Inicia ambiente de desenvolvimento
	@echo "$(GREEN)Iniciando ambiente de desenvolvimento...$(NC)"
	@$(MAKE) dev-backend & $(MAKE) dev-frontend

dev-backend: ## Inicia apenas o backend
	@echo "$(GREEN)Iniciando backend...$(NC)"
	@cd app/backend && uvicorn src.main:app --reload --host 127.0.0.1 --port 8000

dev-frontend: ## Inicia apenas o frontend
	@echo "$(GREEN)Iniciando frontend...$(NC)"
	@cd app/frontend && $(NPM) run dev

test: ## Executa testes
	@echo "$(GREEN)Executando testes...$(NC)"
	@cd app/backend && python -m pytest tests/ -v
	@cd app/frontend && $(NPM) test

test-backend: ## Executa testes do backend
	@echo "$(GREEN)Executando testes do backend...$(NC)"
	@cd app/backend && python -m pytest tests/ -v

test-frontend: ## Executa testes do frontend
	@echo "$(GREEN)Executando testes do frontend...$(NC)"
	@cd app/frontend && $(NPM) test

build: ## Build do projeto
	@echo "$(GREEN)Fazendo build...$(NC)"
	@$(MAKE) build-backend
	@$(MAKE) build-frontend

build-backend: ## Build do backend
	@echo "$(GREEN)Build do backend...$(NC)"
	@cd app/backend && $(PIP) install -r requirements.txt

build-frontend: ## Build do frontend
	@echo "$(GREEN)Build do frontend...$(NC)"
	@cd app/frontend && $(NPM) run build

docker-up: ## Inicia serviços Docker
	@echo "$(GREEN)Iniciando serviços Docker...$(NC)"
	@$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Serviços iniciados!$(NC)"
	@echo "$(YELLOW)Backend: http://localhost:8000$(NC)"
	@echo "$(YELLOW)Frontend: http://localhost:3000$(NC)"
	@echo "$(YELLOW)Redis: localhost:6379$(NC)"
	@echo "$(YELLOW)Prometheus: http://localhost:9090$(NC)"
	@echo "$(YELLOW)Grafana: http://localhost:3001 (admin/admin)$(NC)"

docker-down: ## Para serviços Docker
	@echo "$(GREEN)Parando serviços Docker...$(NC)"
	@$(DOCKER_COMPOSE) down

docker-logs: ## Mostra logs dos serviços Docker
	@$(DOCKER_COMPOSE) logs -f

docker-build: ## Build das imagens Docker
	@echo "$(GREEN)Build das imagens Docker...$(NC)"
	@$(DOCKER_COMPOSE) build

clean: ## Limpa arquivos temporários
	@echo "$(GREEN)Limpando arquivos temporários...$(NC)"
	@find . -type f -name "*.pyc" -delete
	@find . -type d -name "__pycache__" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} +
	@find . -type d -name ".pytest_cache" -exec rm -rf {} +
	@find . -type d -name "node_modules" -exec rm -rf {} +
	@find . -type d -name "dist" -exec rm -rf {} +
	@find . -type d -name "build" -exec rm -rf {} +
	@echo "$(GREEN)Limpeza concluída!$(NC)"

format: ## Formata código
	@echo "$(GREEN)Formatando código...$(NC)"
	@cd app/backend && black src/ tests/
	@cd app/backend && ruff check --fix src/ tests/
	@cd app/frontend && $(NPM) run format

lint: ## Executa linters
	@echo "$(GREEN)Executando linters...$(NC)"
	@cd app/backend && black --check src/ tests/
	@cd app/backend && ruff check src/ tests/
	@cd app/backend && mypy src/
	@cd app/frontend && $(NPM) run lint

check: ## Executa verificações de qualidade
	@echo "$(GREEN)Executando verificações...$(NC)"
	@$(MAKE) lint
	@$(MAKE) test

setup: ## Configuração inicial do projeto
	@echo "$(GREEN)Configurando projeto...$(NC)"
	@cp app/backend/env.example app/backend/.env
	@echo "$(YELLOW)Arquivo .env criado. Configure as variáveis de ambiente.$(NC)"
	@$(MAKE) install
	@echo "$(GREEN)Configuração concluída!$(NC)"

deploy-dev: ## Deploy em ambiente de desenvolvimento
	@echo "$(GREEN)Deploy em desenvolvimento...$(NC)"
	@$(MAKE) docker-build
	@$(MAKE) docker-up

deploy-prod: ## Deploy em produção (preparação)
	@echo "$(RED)Deploy em produção...$(NC)"
	@echo "$(YELLOW)Verifique as configurações de produção!$(NC)"
	@$(MAKE) build
	@$(MAKE) docker-build

logs: ## Mostra logs da aplicação
	@echo "$(GREEN)Logs da aplicação:$(NC)"
	@$(DOCKER_COMPOSE) logs -f backend

status: ## Status dos serviços
	@echo "$(GREEN)Status dos serviços:$(NC)"
	@$(DOCKER_COMPOSE) ps

restart: ## Reinicia serviços
	@echo "$(GREEN)Reiniciando serviços...$(NC)"
	@$(DOCKER_COMPOSE) restart

update: ## Atualiza dependências
	@echo "$(GREEN)Atualizando dependências...$(NC)"
	@cd app/backend && $(PIP) install --upgrade -r requirements.txt
	@cd app/frontend && $(NPM) update

# Comandos específicos para desenvolvimento
dev-full: ## Ambiente completo com monitoramento
	@$(MAKE) docker-up
	@echo "$(GREEN)Ambiente completo iniciado!$(NC)"

dev-minimal: ## Ambiente mínimo (apenas backend e Redis)
	@$(DOCKER_COMPOSE) up -d backend redis
	@echo "$(GREEN)Ambiente mínimo iniciado!$(NC)"

# Comandos específicos do frontend
frontend-dev: ## Inicia frontend em modo desenvolvimento
	@echo "$(GREEN)🚀 Iniciando frontend...$(NC)"
	@cd app/frontend && $(NPM) run dev

frontend-build: ## Builda frontend para produção
	@echo "$(GREEN)🔨 Buildando frontend...$(NC)"
	@cd app/frontend && $(NPM) run build

frontend-test: ## Executa testes do frontend
	@echo "$(GREEN)🧪 Testando frontend...$(NC)"
	@cd app/frontend && $(NPM) test

frontend-test-coverage: ## Executa testes com cobertura do frontend
	@echo "$(GREEN)📊 Testes com cobertura do frontend...$(NC)"
	@cd app/frontend && $(NPM) run test:coverage

frontend-test-ui: ## Executa testes com UI do frontend
	@echo "$(GREEN)🖥️ Testes com UI do frontend...$(NC)"
	@cd app/frontend && $(NPM) run test:ui

frontend-lint: ## Executa linting do frontend
	@echo "$(GREEN)🔍 Linting do frontend...$(NC)"
	@cd app/frontend && $(NPM) run lint

frontend-format: ## Formata código do frontend
	@echo "$(GREEN)✨ Formatando frontend...$(NC)"
	@cd app/frontend && $(NPM) run format

frontend-type-check: ## Verifica tipos do frontend
	@echo "$(GREEN)🔍 Verificando tipos do frontend...$(NC)"
	@cd app/frontend && $(NPM) run type-check

# Comandos de debug
debug-backend: ## Debug do backend
	@echo "$(GREEN)Debug do backend...$(NC)"
	@cd app/backend && python -m pdb -m uvicorn src.main:app --reload

shell: ## Shell Python do backend
	@echo "$(GREEN)Shell Python...$(NC)"
	@cd app/backend && python

# Comandos de documentação
docs: ## Gera documentação
	@echo "$(GREEN)Gerando documentação...$(NC)"
	@cd app/backend && python -m pdoc src/ --html --output-dir docs/

# Comandos de backup
backup: ## Backup dos dados
	@echo "$(GREEN)Backup dos dados...$(NC)"
	@$(DOCKER_COMPOSE) exec backend python -c "from src.adapters.dependencies import get_dependency_container; print('Backup iniciado')"

# Comandos de monitoramento
monitor: ## Inicia monitoramento
	@echo "$(GREEN)Iniciando monitoramento...$(NC)"
	@$(DOCKER_COMPOSE) up -d prometheus grafana

# Comandos de segurança
security-check: ## Verificação de segurança
	@echo "$(GREEN)Verificação de segurança...$(NC)"
	@cd app/backend && safety check
	@cd app/frontend && $(NPM) audit

# Comandos de performance
benchmark: ## Testes de performance
	@echo "$(GREEN)Testes de performance...$(NC)"
	@cd app/backend && python -m pytest tests/ -m "performance" -v

# Comandos de CI/CD
ci: ## Pipeline de CI
	@echo "$(GREEN)Executando pipeline de CI...$(NC)"
	@$(MAKE) check
	@$(MAKE) test
	@$(MAKE) build

# Comandos de limpeza específicos
clean-docker: ## Limpa containers e volumes Docker
	@echo "$(GREEN)Limpando Docker...$(NC)"
	@$(DOCKER_COMPOSE) down -v
	@$(DOCKER) system prune -f

clean-all: ## Limpeza completa
	@echo "$(GREEN)Limpeza completa...$(NC)"
	@$(MAKE) clean
	@$(MAKE) clean-docker

# Comandos de ajuda específicos
help-backend: ## Ajuda específica do backend
	@echo "$(GREEN)Comandos do Backend:$(NC)"
	@echo "  dev-backend     - Inicia backend em modo desenvolvimento"
	@echo "  test-backend    - Executa testes do backend"
	@echo "  build-backend   - Build do backend"
	@echo "  debug-backend   - Debug do backend"
	@echo "  shell           - Shell Python"

help-frontend: ## Ajuda específica do frontend
	@echo "$(GREEN)Comandos do Frontend:$(NC)"
	@echo "  dev-frontend    - Inicia frontend em modo desenvolvimento"
	@echo "  test-frontend   - Executa testes do frontend"
	@echo "  build-frontend  - Build do frontend"

help-docker: ## Ajuda específica do Docker
	@echo "$(GREEN)Comandos do Docker:$(NC)"
	@echo "  docker-up       - Inicia serviços Docker"
	@echo "  docker-down     - Para serviços Docker"
	@echo "  docker-build    - Build das imagens"
	@echo "  docker-logs     - Mostra logs"
	@echo "  status          - Status dos serviços"
