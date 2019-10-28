FROM python:3.7-alpine AS base

RUN apk update
RUN apk add bash

ENV PYTHONPATH=/src/processor

ENV PYTHONDONTWRITEBYTECODE=1

COPY devops/docker/install-clamav.sh install-clamav.sh
RUN sh install-clamav.sh

COPY devops/docker/install.sh install.sh
RUN sh install.sh

COPY devops/docker/clamd.conf /etc/clamav/clamd.conf

ENTRYPOINT ["/src/docker/scripts/entrypoint.sh"]

FROM base AS base_dev
# no need to copy src directory for dev mode as it is mounted as a volume
WORKDIR /src
COPY src/requirements.*.txt ./
RUN pip install -r requirements.dev.txt -r requirements.txt

FROM base AS build

COPY ./src /src
WORKDIR /src

RUN pip install -r requirements.txt
