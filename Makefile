PYTHON_FILES := tests
MAX_CONCURRENCY ?= 1

check-swarm-init:
	@if [ "$$(docker info --format '{{.Swarm.LocalNodeState}}')" != "active" ]; then \
        echo "Docker is not part of a swarm. Initializing..."; \
        docker swarm init; \
    else \
        echo "Docker is already part of a swarm."; \
    fi

.PHONY: code
code: check format lint sort bandit test

.PHONY: check
check:
	poetry run mypy $(PYTHON_FILES)

.PHONY: format
format:
	poetry run yapf --in-place --recursive $(PYTHON_FILES)

.PHONY: format-check
format-check:
	poetry run yapf --diff --recursive $(PYTHON_FILES)

.PHONY: lint
lint:
	poetry run flake8 $(PYTHON_FILES)

.PHONY: sort
sort:
	poetry run isort --force-single-line-imports $(PYTHON_FILES)

.PHONY: sort-check
sort-check:
	poetry run isort --force-single-line-imports $(PYTHON_FILES) --check-only

.PHONY: bandit
bandit:
	poetry run bandit -r $(PYTHON_FILES) --quiet --configfile=.bandit

.PHONY: bandit-check
bandit-check:
	poetry run bandit -r $(PYTHON_FILES) --configfile=.bandit

# ACTIONS_RUNNER_DEBUG is used in github actions
.PHONY: test
test:
	@if [ "$(DEBUG)" = "true" ] || [ "$(ACTIONS_RUNNER_DEBUG)" = "true" ]; then \
        export DEBUG=true; \
        LOG_LEVEL="--log-cli-level=debug"; \
    else \
        LOG_LEVEL=""; \
    fi; \
	poetry run pytest -s -o log_cli=True $$LOG_LEVEL -n ${MAX_CONCURRENCY} tests

.PHONY: coverage
coverage:
	@if [ "$(DEBUG)" = "true" ] || [ "$(ACTIONS_RUNNER_DEBUG)" = "true" ]; then \
        export DEBUG=true; \
        LOG_LEVEL="--log-cli-level=debug"; \
    else \
        LOG_LEVEL=""; \
    fi; \
	poetry run pytest -r -o log_cli=True $$LOG_LEVEL -n ${MAX_CONCURRENCY} --cov-report term-missing --cov=pantos tests
