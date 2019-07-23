FROM python:3.7-alpine

COPY ./requirements.txt /archiver/requirements.txt
COPY ./docker/install.sh /archiver/docker/install.sh

RUN sh archiver/docker/install.sh

COPY . /archiver

WORKDIR /archiver

ENV PYTHONPATH=/archiver/src
ENV PYTHONDONTWRITEBYTECODE=1

CMD sh docker/cmd.sh
