.PHONY: run
.ONESHELL:
run:
	@ docker-compose up --build --remove-orphans


.PHONY: ssh-project
.ONESHELL:
ssh-project:
	@ docker container exec -it psd-project /bin/sh
