.PHONY: run
.ONESHELL:
run:
	DEBUG=True PYTHONPATH=$(PYTHONPATH):./project python project/function
