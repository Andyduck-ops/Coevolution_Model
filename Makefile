.PHONY: bootstrap lint test build check all

bootstrap:
	bash .harness/scripts/bootstrap_env.sh

lint:
	.venv/bin/python -m ruff check src tests

test:
	.venv/bin/python -m pytest -q

build:
	.venv/bin/python -m compileall -q src

check: lint test build

all: bootstrap check
