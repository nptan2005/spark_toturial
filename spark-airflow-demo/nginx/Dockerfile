FROM nginx:latest

RUN rm -rf /etc/nginx/conf.d/* \
    && rm -rf /docker-entrypoint.d/*

COPY nginx.conf /etc/nginx/nginx.conf
COPY conf.d/ /etc/nginx/conf.d/
RUN mkdir -p /etc/nginx/stream.d
COPY stream.d/ /etc/nginx/stream.d/
