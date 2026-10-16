SHELL := /bin/bash

.DEFAULT_GOAL := help

CLIENT_DIR := client
SERVER_DIR := server

PYTHON ?= python3.12
VENV := $(SERVER_DIR)/.python-venv
PIP := $(VENV)/bin/pip
FLASK := $(VENV)/bin/flask

FLASK_SERVER_IP ?= localhost
FLASK_SERVER_PORT ?= 8000
FLASK_SERVER_WEB_SOCKET_PORT ?= 8001

VITE_CLIENT_IP ?= localhost
VITE_CLIENT_PORT ?= 8002
VITE_LOG_LEVEL ?= error

DATABASE_FILE_NAME ?= QView.db

-include .env

export FLASK_SERVER_IP
export FLASK_SERVER_PORT
export FLASK_SERVER_WEB_SOCKET_PORT
export VITE_CLIENT_IP
export VITE_CLIENT_PORT
export VITE_LOG_LEVEL
export DATABASE_FILE_NAME

.PHONY: help setup ensure-config ensure-setup backend frontend dev build reset-db fresh-dev clean

help: 
	@echo "QView3D commands:"
	@echo "  make setup      - Install project dependencies"
	@echo "  make dev        - Start frontend and backend"
	@echo "  make build      - Build frontend for production"
	@echo "  make reset-db   - Reset the SQLite database"
	@echo "  make fresh-dev  - Reset database and start development"
	@echo "  make clean      - Remove generated frontend build"

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
	cd $(SERVER_DIR) && \
	FLASK_RUN_HOST="$(FLASK_SERVER_IP)" \
	FLASK_RUN_PORT="$(FLASK_SERVER_PORT)" \
	.python-venv/bin/flask run

frontend: ensure-setup
	cd $(CLIENT_DIR) && \
	npm run dev -- \
		--host "$(VITE_CLIENT_IP)" \
		--port "$(VITE_CLIENT_PORT)" \
		--cors \
		--logLevel "$(VITE_LOG_LEVEL)"

dev: ensure-setup
	$(MAKE) -j2 backend frontend

build: ensure-setup
	cd $(CLIENT_DIR) && npm run build

reset-db:
	rm -f "$(SERVER_DIR)/$(DATABASE_FILE_NAME)"
	@echo "Database reset: $(SERVER_DIR)/$(DATABASE_FILE_NAME)"

fresh-dev: reset-db dev

clean:
	rm -rf "$(CLIENT_DIR)/dist"
	@echo "Frontend build removed."