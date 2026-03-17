#!/bin/sh
set -eu

# Helper: shell-escape a value by replacing ' with '\''
esc() { printf '%s' "$1" | sed "s/'/'\\\\''/g"; }

# Bake current env vars into a wrapper so crond inherits them.
# Values are escaped to prevent shell injection from special characters.
{
  printf '#!/bin/sh\n'
  printf "export OL_INSTANCE='%s'\n"          "$(esc "${OL_INSTANCE:-}")"
  printf "export OL_ADMIN_EMAIL='%s'\n"       "$(esc "${OL_ADMIN_EMAIL:-}")"
  printf "export OL_ADMIN_PASSWORD='%s'\n"    "$(esc "${OL_ADMIN_PASSWORD:-}")"
  printf "export DAILY_MESSAGE_ENABLED='%s'\n" "$(esc "${DAILY_MESSAGE_ENABLED:-true}")"
  printf "export DAILY_SYSTEM_MESSAGE='%s'\n" "$(esc "${DAILY_SYSTEM_MESSAGE:-}")"
  printf 'exec python /daily_message_job.py\n'
} > /usr/local/bin/run-daily-message.sh
chmod 700 /usr/local/bin/run-daily-message.sh

# busybox crond uses /var/spool/cron/crontabs/<user> (no username field)
mkdir -p /var/spool/cron/crontabs
printf 'CRON_TZ=Europe/Stockholm\n0 6 * * * /usr/local/bin/run-daily-message.sh >> /proc/1/fd/1 2>&1\n' \
  > /var/spool/cron/crontabs/root

crond -b
exec gunicorn wsgi:app --bind 0.0.0.0:8000
