FROM python:3.7-alpine AS base

RUN apk update

ENV PYTHONPATH=/src/processor

ENV PYTHONDONTWRITEBYTECODE=1

COPY devops/docker/install-clamav.sh install-clamav.sh
RUN sh install-clamav.sh

COPY devops/docker/install.sh install.sh
COPY devops/docker/cmd.sh cmd.sh
RUN sh install.sh

COPY devops/docker/clamd.conf /etc/clamav/clamd.conf

ENTRYPOINT ["/cmd.sh"]

CMD ["tail", "-f", "/dev/null"]

FROM base AS base_dev
# no need to copy src directory for dev mode as it is mounted as a volume
WORKDIR /src
COPY src/requirements.txt requirements.txt
RUN pip install -r requirements.txt

FROM base AS build

COPY ./src /src
WORKDIR /src

RUN pip install -r requirements.txt
