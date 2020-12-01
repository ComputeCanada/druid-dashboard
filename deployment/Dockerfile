FROM alpine:latest
MAINTAINER Drew Leske <drew.leske@computecanada.ca>

#ENV WERKZEUG_DEBUG_PIN 'off'
#ENV FLASK_ENV=development
ENV PYTHONPATH '/home/beam'

# install base OS stuff
RUN adduser -s /sbin/nologin -D -h /home/beam beam
RUN apk --update add python3 postgresql-dev build-base python3-dev openldap-dev py3-pip

# install Flask
COPY requirements.txt /tmp/
RUN pip3 install --upgrade -r /tmp/requirements.txt

# clean up
RUN apk del build-base python3-dev gmp-dev openldap-dev && \
  rm -rf /root/.cache/pip/* && \
  rm -rf /var/cache/apk/* && \
  rm -rf /tmp/*

# install application
WORKDIR /home/beam
RUN mkdir beam ccldap
COPY ccldap/ ccldap/
COPY app/ app/
RUN pybabel compile -d app/translations
ENV FLASK_APP=/home/beam/app

EXPOSE 5000
USER beam

CMD flask run --with-threads --host=0.0.0.0
