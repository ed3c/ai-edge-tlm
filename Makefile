.PHONY: install validate test check

install:
	python -m pip install -e '.[dev]'

validate:
	edge-tlmctl validate
	edge-tlmctl audit-public-boundary

test:
	pytest -q

check: validate test
