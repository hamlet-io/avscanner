FROM python:3.7-alpine AS base

RUN apk update && apk add \
    bash make zip \
    clamav clamav-dev

RUN chown clamav:clamav /var/lib/clamav && \
        mkdir /var/run/clamav && chown clamav:clamav /var/run/clamav && \
        chmod 755 /var/run/clamav

RUN echo "Updating AV Definitions ${date}" && freshclam -v -u clamav

ENV PYTHONPATH=/src/processor
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install --upgrade pip
COPY devops/docker/clamd.conf /etc/clamav/clamd.conf
ENTRYPOINT ["/src/docker/scripts/entrypoint.sh"]

FROM base AS base_dev
# no need to copy src directory for dev mode as it is mounted as a volume
WORKDIR /src
COPY src/requirements*.txt ./
RUN pip install -r requirements.dev.txt -r requirements.txt

FROM base AS build

COPY ./src /src
WORKDIR /src

RUN pip install -r requirements.txt
