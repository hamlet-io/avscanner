FROM python:3.7-alpine

RUN apk update

COPY ./docker/install-clamav.sh /processor/docker/install-clamav.sh
RUN sh processor/docker/install-clamav.sh

COPY ./requirements.txt /processor/requirements.txt
COPY ./docker/install.sh /processor/docker/install.sh
RUN sh processor/docker/install.sh

COPY ./docker/clamd.conf /etc/clamav/clamd.conf

COPY . /processor

WORKDIR /processor

ENV PYTHONPATH=/processor/src
ENV PYTHONDONTWRITEBYTECODE=1

CMD sh docker/cmd.sh
