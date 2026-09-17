FROM nginx:alpine
COPY dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN chown -R 10001:10001 /var/cache/nginx /var/run /run /var/log/nginx /usr/share/nginx/html /etc/nginx

USER 10001

EXPOSE 3001

