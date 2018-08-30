FROM python:alpine


RUN apk add git && apk add vim && apk upgrade
#RUN set -ex apk add --no-cache sqlite-dev


RUN apk update
VOLUME /ReviewSystem
WORKDIR /ReviewSystem
COPY . /



RUN pip install -r /requirements.txt


EXPOSE 8000

WORKDIR /review_project

#RUN mkdir ratings/migrations

RUN touch ratings/migrations/__init__.py

COPY ./docker-entrypoint.sh /

RUN ["chmod", "+x", "/docker-entrypoint.sh"]
