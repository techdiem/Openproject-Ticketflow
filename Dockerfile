FROM alpine:latest

RUN apk add --no-cache python3 py3-pip bash curl

ENV CRON_SCHEDULE="*/5 6-19 * * 1-5"

COPY app /app
RUN rm /usr/lib/python*/EXTERNALLY-MANAGED && pip3 install --no-cache-dir -r /app/requirements.txt

RUN echo "CRON_PLACEHOLDER python3 /app/ticketflow.py >> /proc/1/fd/1 2>> /proc/1/fd/2" > /etc/crontabs/root.template

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

USER 0
CMD ["/entrypoint.sh"]
