set shell := ["bash", "-euo", "pipefail", "-c"]

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

hook-replay:
    bash .harness/scripts/hook_replay.sh

ops:
    bash .harness/scripts/opsctl.sh full-check --strict

governance:
    bash .harness/scripts/opsctl.sh governance-check --strict

check: lint test build e2e hook-replay governance

all: bootstrap check
