SHELL := /bin/bash

.DEFAULT_GOAL := help

CLIENT_DIR := client
SERVER_DIR := server

PYTHON ?= python3.12
VENV := $(SERVER_DIR)/.python-venv
PIP := $(VENV)/bin/pip
FLASK := $(VENV)/bin/flask

ENV_FILE := .env
ENV_EXAMPLE := .env.example

.PHONY: help ensure-config setup ensure-setup backend frontend dev build reset-db fresh-dev clean check-serial production-check production-config production-backend production-frontend production

help: 
	@echo "QView3D commands:"
	@echo "  make setup      - Install project dependencies"
	@echo "  make dev        - Start frontend and backend"
	@echo "  make build      - Build frontend for production"
	@echo "  make reset-db   - Reset the SQLite database"
	@echo "  make fresh-dev  - Reset database and start development"
	@echo "  make clean      - Remove generated frontend build"
	@echo "  make production - Build and run QView3D in production mode"
	@echo "  make check-serial - Check Linux printer serial permissions"

ensure-config:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env from .env.example"; \
	fi

setup: ensure-config 
	@command -v $(PYTHON) >/dev/null 2>&1 || { \
		echo "Error: $(PYTHON) is not installed."; \
		exit 1; \
	}
	@command -v npm >/dev/null 2>&1 || { \
		echo "Error: npm is not installed."; \
		exit 1; \
	}
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r $(SERVER_DIR)/dependencies.txt
	cd $(CLIENT_DIR) && npm install

ensure-setup: ensure-config 
	@if [ ! -x "$(FLASK)" ] || [ ! -d "$(CLIENT_DIR)/node_modules" ]; then \
		echo "Dependencies are missing. Running setup..."; \
		$(MAKE) setup; \
	fi

backend: ensure-setup
	@set -a; source "$(ENV_FILE)"; set +a; \
	cd "$(SERVER_DIR)" && \
	FLASK_RUN_HOST="$$FLASK_SERVER_IP" \
	FLASK_RUN_PORT="$$FLASK_SERVER_PORT" \
	.python-venv/bin/flask run

frontend: ensure-setup
	@set -a; source "$(ENV_FILE)"; set +a; \
	cd "$(CLIENT_DIR)" && \
	npm run dev -- \
		--host "$$VITE_CLIENT_IP" \
		--port "$$VITE_CLIENT_PORT" \
		--cors \
		--logLevel "$$VITE_LOG_LEVEL"

dev: ensure-setup
	$(MAKE) -j2 backend frontend

build: ensure-setup
	@set -a; source "$(ENV_FILE)"; set +a; \
	cd "$(CLIENT_DIR)" && npm run build

reset-db: ensure-config
	@set -a; source "$(ENV_FILE)"; set +a; \
	rm -f "$(SERVER_DIR)/$$DATABASE_FILE_NAME"; \
	echo "Database reset: $(SERVER_DIR)/$$DATABASE_FILE_NAME"

fresh-dev: reset-db dev

clean:
	rm -rf "$(CLIENT_DIR)/dist"
	@echo "Frontend build removed."

check-serial: ensure-config
	@set -a; source "$(ENV_FILE)"; set +a; \
	if id -nG "$$USER" | tr ' ' '\n' | grep -qx "$$SERIAL_GROUP"; then \
		echo "Serial permission OK: $$USER is in $$SERIAL_GROUP"; \
	else \
		echo "ERROR: $$USER is not in the $$SERIAL_GROUP group."; \
		echo "Run: sudo usermod -aG $$SERIAL_GROUP $$USER"; \
		echo "Then log out and log back in."; \
		exit 1; \
	fi

production-check: ensure-setup
	@command -v nginx >/dev/null 2>&1 || { \
		echo "ERROR: nginx is not installed."; \
		echo "Install it with: sudo apt install nginx"; \
		exit 1; \
	}
	@test -x "$(VENV)/bin/gunicorn" || { \
		echo "ERROR: Gunicorn is not installed."; \
		echo "Run make setup."; \
		exit 1; \
	}

production-config: ensure-config
	@mkdir -p .nginx/logs
	@set -a; source "$(ENV_FILE)"; set +a; \
	sed \
		-e "s|__FRONTEND_IP__|$$PRODUCTION_FRONTEND_IP|g" \
		-e "s|__FRONTEND_PORT__|$$PRODUCTION_FRONTEND_PORT|g" \
		-e "s|__DIST_PATH__|$(CURDIR)/$(CLIENT_DIR)/dist|g" \
		deploy/nginx.conf.template > .nginx/nginx.conf
	@echo "Generated production Nginx configuration."

production-backend:
	@set -a; source "$(ENV_FILE)"; set +a; \
	cd "$(SERVER_DIR)" && \
	.python-venv/bin/gunicorn \
		--bind "$$PRODUCTION_BACKEND_IP:$$PRODUCTION_BACKEND_PORT" \
		--workers "$$GUNICORN_WORKERS" \
		--threads "$$GUNICORN_THREADS" \
		"$$GUNICORN_APP"

production-frontend:
	nginx \
		-p "$(CURDIR)/.nginx/" \
		-c nginx.conf \
		-g "daemon off;"

production: production-check check-serial build production-config
	$(MAKE) -j2 production-backend production-frontend