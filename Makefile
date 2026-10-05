.PHONY: install seed test run-backend run-frontend run build

PYTHON ?= python

install:
	$(PYTHON) -m pip install -r backend/requirements.txt
	cd frontend && npm install

seed:
	$(PYTHON) -m backend.app.sim.seed

test:
	$(PYTHON) -m pytest backend/tests/ -v

eval:
	$(PYTHON) -m backend.app.eval.qa_benchmark

run-backend:
	$(PYTHON) -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

run:
	$(PYTHON) -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
