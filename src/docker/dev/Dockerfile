FROM python:3.7-alpine

WORKDIR /src

ENV PYTHONPATH=/src/processor

ENV PYTHONDONTWRITEBYTECODE=1

RUN apk update

COPY docker/dev/install-clamav.sh docker/dev/install-clamav.sh
RUN sh docker/dev/install-clamav.sh

COPY requirements.txt requirements.txt
COPY docker/dev/install.sh docker/dev/install.sh
RUN sh docker/dev/install.sh

COPY docker/dev/clamd.conf /etc/clamav/clamd.conf

ENTRYPOINT ["/src/docker/dev/cmd.sh"]

CMD ["tail", "-f", "/dev/null"]