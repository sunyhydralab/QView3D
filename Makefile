PYTHON=python3.12
VENV=server/.python-venv
PIP=$(VENV)/bin/pip

.PHONY: setup backend frontend dev build clean

setup:
	$(PYTHON) -m venv $(VENV)
	$(PIP) install -r server/dependencies.txt
	cd client && npm install

backend:
	cd server && .python-venv/bin/flask run --port 8000

frontend:
	cd client && npm run dev -- --port 8002

dev:
	$(MAKE) -j2 backend frontend

build:
	cd client && npm run build

clean:
	rm -rf client/dist 