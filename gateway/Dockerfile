FROM nginx:1.25-alpine

COPY nginx.conf /etc/nginx/nginx.conf

RUN chown -R 10001:10001 /var/cache/nginx /var/run /run /var/log/nginx /etc/nginx

USER 10001


EXPOSE 80

