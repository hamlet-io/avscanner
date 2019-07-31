FROM python:3.7-alpine

WORKDIR /archiver

ENV PYTHONPATH=/archiver/src:/common/src
ENV PYTHONDONTWRITEBYTECODE=1


COPY archiver/requirements requirements
COPY archiver/docker/dev/install.sh  docker/dev/install.sh

RUN sh docker/dev/install.sh

COPY archiver ./

COPY ./common /common

CMD sh docker/dev/cmd.sh
