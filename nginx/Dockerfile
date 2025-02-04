FROM nginx:stable-alpine

ARG DOMAIN
ARG CONF_NAME=ssl

COPY includes /etc/nginx/includes
COPY $CONF_NAME.conf /etc/nginx/conf.d/default.conf

RUN sed -i "s/__DOMAIN__/$DOMAIN/g" /etc/nginx/conf.d/default.conf
