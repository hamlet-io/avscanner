FROM python:3.7-alpine

WORKDIR /virus-scanner

ENV PYTHONPATH=/virus-scanner/src
ENV PYTHONDONTWRITEBYTECODE=1

RUN apk update

COPY ./docker/dev/install-clamav.sh docker/dev/install-clamav.sh
RUN sh docker/dev/install-clamav.sh

COPY ./requirements requirements
COPY ./docker/dev/install.sh docker/dev/install.sh
RUN sh docker/dev/install.sh

COPY ./docker/dev/clamd.conf /etc/clamav/clamd.conf

CMD sh docker/dev/cmd.sh
