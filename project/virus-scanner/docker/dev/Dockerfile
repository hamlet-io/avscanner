FROM python:3.7-alpine

WORKDIR /virus-scanner

ENV PYTHONPATH=/virus-scanner/src:/common/src
ENV PYTHONDONTWRITEBYTECODE=1

RUN apk update

COPY virus-scanner/docker/dev/install-clamav.sh docker/dev/install-clamav.sh
RUN sh docker/dev/install-clamav.sh

COPY virus-scanner/requirements requirements
COPY virus-scanner/docker/dev/install.sh docker/dev/install.sh
RUN sh docker/dev/install.sh

COPY virus-scanner/docker/dev/clamd.conf /etc/clamav/clamd.conf

COPY common /common

CMD sh docker/dev/cmd.sh
