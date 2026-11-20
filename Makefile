PYTHON ?= python
.PHONY: backend-lint backend-typecheck backend-test frontend-lint frontend-typecheck frontend-test test review
backend-lint:
	$(PYTHON) -m ruff check fur_empire tests scripts
	$(PYTHON) -m black --check fur_empire tests scripts
backend-typecheck:
	$(PYTHON) -m mypy fur_empire
backend-test:
	$(PYTHON) -m pytest -q
frontend-lint:
	npm run lint
frontend-typecheck:
	npm run check
frontend-test:
	npm test
test: backend-lint backend-typecheck backend-test frontend-lint frontend-typecheck frontend-test
review:
	$(PYTHON) -m fur_empire.manage readiness
