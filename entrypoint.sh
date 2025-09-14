#!/bin/sh

sed "s|CRON_PLACEHOLDER|${CRON_SCHEDULE}|" /etc/crontabs/root.template > /etc/crontabs/root

echo "Starting OpenProject ticket-bot"
echo "Ticketflow sync cron schedule: ${CRON_SCHEDULE}"

exec crond -f