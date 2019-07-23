FROM python:3.7-alpine

COPY ./requirements.txt /project/requirements.txt
COPY ./docker/install.sh /project/docker/install.sh

RUN sh project/docker/install.sh

COPY . /project

WORKDIR /project

ENV PYTHONPATH=/project
ENV PYTHONDONTWRITEBYTECODE=1

CMD sh docker/cmd.sh
