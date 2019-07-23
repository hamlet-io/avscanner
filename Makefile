.PHONY: run
.ONESHELL:
run:
	@ docker-compose up --build --remove-orphans
