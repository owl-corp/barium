# Serves a prebuilt dist/ (see README "Container image"). The logs are private,
# so dist/ is built locally from the Mongo export, never in CI.
FROM docker.io/nginxinc/nginx-unprivileged:stable-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY dist/ /usr/share/nginx/html/
