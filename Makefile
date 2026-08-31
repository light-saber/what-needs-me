PYTHON := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: install test run

install:
	python3.11 -m venv .venv
	$(PIP) install -r requirements.txt

test:
	$(PYTHON) -m pytest

run:
	$(PYTHON) -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
