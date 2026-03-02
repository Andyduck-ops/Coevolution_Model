.PHONY: bootstrap lint test build e2e check all

bootstrap:
	bash .harness/scripts/bootstrap_env.sh

lint:
	.venv/bin/python -m ruff check src tests

test:
	.venv/bin/python -m pytest -q

build:
	.venv/bin/python -m compileall -q src

e2e:
	bash .harness/scripts/e2e_smoke.sh

check: lint test build e2e

all: bootstrap check
