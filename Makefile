.PHONY: validate test lint

validate:
	python scripts/validate_config.py --config configs/defaults.yml
	python scripts/validate_workflows.py

test:
	python -m unittest discover -s tests -v

lint:
	ruff check scripts tests
