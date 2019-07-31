.PHONY: run
.ONESHELL:
run:
	@ python src

.PHONY: test-unit
.ONESHELL:
test-unit:
	@ pytest tests/unit -vv

.PHONY: test-integration
.ONESHELL:
test-integration:
	@ pytest tests/integration -vv


.PHONY: coverage
.ONESHELL:
coverage:
		coverage run -m tests
		coverage report -m
		coverage html
