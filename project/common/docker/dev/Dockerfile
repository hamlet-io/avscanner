FROM python:3.7-alpine

WORKDIR /common

ENV PYTHONPATH=/common/src
ENV PYTHONDONTWRITEBYTECODE=1

COPY common/requirements requirements
COPY common/docker/dev/install.sh  docker/dev/install.sh

RUN sh docker/dev/install.sh

COPY . ./


CMD sh docker/dev/cmd.sh
