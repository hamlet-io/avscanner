.PHONY: clean
.ONESHELL:
clean:
	@ docker-compose down --rmi all --volumes

.PHONY: run
.ONESHELL:
run:
	@ docker-compose up --build --remove-orphans -d

.PHONY: run-fg
.ONESHELL:
run-fg:
	@ docker-compose up --build --remove-orphans

.PHONY: build
.ONESHELL:
build:
	@ docker-compose build --no-cache


.PHONY: ssh-project
.ONESHELL:
ssh-processor:
	@ docker-compose exec processor /bin/sh


.PHONY: ci
.ONESHELL:
ci:
	@ dockerstagedir=${dockerstagedir} docker-compose --no-ansi down --rmi local --volumes
	@ dockerstagedir=${dockerstagedir} docker-compose --no-ansi -f docker-compose.yml -f docker-compose.ci.yml up --build --remove-orphans --exit-code-from processor
	EXIT_CODE=$$?;\
    echo "command exited with $$EXIT_CODE";\
	dockerstagedir=${dockerstagedir} docker-compose --no-ansi down --rmi local --volumes;\
    exit $$EXIT_CODE
