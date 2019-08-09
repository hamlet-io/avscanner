.PHONY: run
.ONESHELL:
run:
	@ docker-compose up --build --remove-orphans

.PHONY: build
.ONESHELL:
build:
	@ docker-compose build --no-cache


.PHONY: ssh-project
.ONESHELL:
ssh-project:
	@ docker container exec -it psd-processor /bin/sh


.PHONY: ci
.ONESHELL:
ci:
	@ docker-compose down --rmi local --volumes
	@ docker-compose -f docker-compose.yml -f docker-compose.ci.yml up --build --remove-orphans --exit-code-from processor
