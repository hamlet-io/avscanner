FROM python:3.7-alpine

WORKDIR /validator

ENV PYTHONPATH=/validator/src:/common/src
ENV PYTHONDONTWRITEBYTECODE=1

COPY validator/requirements requirements
COPY validator/docker/dev/install.sh  docker/dev/install.sh

RUN sh docker/dev/install.sh

COPY . ./

COPY common /common

CMD sh docker/dev/cmd.sh
