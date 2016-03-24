FROM python:3.4

MAINTAINER Michael Glukhovsky, mike@rethinkdb.com

RUN apt-get update && \
    apt-get autoremove && \
    apt-get autoclean && \
    apt-get -y install nginx-full && \
    apt-get -y install build-essential python-dev python-pip supervisor && \
    pip install --upgrade pip

RUN mkdir -p /srv/www/horizon.io
