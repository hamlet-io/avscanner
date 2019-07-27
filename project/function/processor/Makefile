.PHONY: run
.ONESHELL:
run:
	@ python src

.PHONY: test-unit
.ONESHELL:
test-unit:
	@ pytest tests/unit

test-integration:
	@ pytest tests/integration


.PHONY: coverage
.ONESHELL:
coverage:
		coverage run -m tests
		coverage report -m
		coverage html
