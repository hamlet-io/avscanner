.PHONY: run
.ONESHELL:
run:
	@ docker-compose up --build --remove-orphans


.PHONY: ssh-validator
.ONESHELL:
ssh-validator:
	@ docker container exec -it psd-validator /bin/sh


.PHONY: ssh-archiver
.ONESHELL:
ssh-archiver:
	@ docker container exec -it psd-archiver /bin/sh


.PHONY: ssh-virus-scanner
.ONESHELL:
ssh-virus-scanner:
	@ docker container exec -it psd-virus-scanner /bin/sh
