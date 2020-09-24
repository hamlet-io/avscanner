.PHONY: demo
.ONESHELL:
demo:
	@ pytest tests/integration/worker/test_cooperation.py -x -vv

.PHONY: test-unit
.ONESHELL:
test-unit:
	@ pytest tests/unit -vv -x

.PHONY: test-integration
.ONESHELL:
test-integration:
	@ pytest tests/integration -vv -x


.PHONY: coverage
.ONESHELL:
coverage:
		coverage run -m tests
		coverage report -m
		coverage html


.PHONY: test-ci
.ONESHELL:
test-ci:

	@ python -m pytest tests --junitxml=test-report.xml --cov --cov-report=xml
