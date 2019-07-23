FROM python:3.7-alpine

COPY ./requirements.txt /processor/requirements.txt
COPY ./docker/install.sh /processor/docker/install.sh

RUN sh processor/docker/install.sh

COPY . /processor

WORKDIR /processor

ENV PYTHONPATH=/processor/src
ENV PYTHONDONTWRITEBYTECODE=1

CMD sh docker/cmd.sh
