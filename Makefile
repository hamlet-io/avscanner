.PHONY: run
.ONESHELL:
run:
	@ docker-compose up --build --remove-orphans


.PHONY: run
.ONESHELL:
ssh-processor:
	@ docker container exec -it passport-scanner-data-processor /bin/sh


.PHONY: run
.ONESHELL:
ssh-archiver:
	@ docker container exec -it passport-scanner-data-archiver /bin/sh
