FROM python:3.7-alpine

WORKDIR /validator

ENV PYTHONPATH=/validator/src
ENV PYTHONDONTWRITEBYTECODE=1

COPY ./requirements requirements
COPY ./docker/dev/install.sh  docker/dev/install.sh

RUN sh docker/dev/install.sh

COPY . ./


CMD sh docker/dev/cmd.sh
