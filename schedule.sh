#!/bin/bash

SCRIPT_PATH="$HOME/Documents/GitHub/epollo/run_screenshots.sh"
LOG_PATH="/tmp/epollo_cron.log"

CRON_CMD="*/10 * * * * $SCRIPT_PATH >> $LOG_PATH 2>&1"

EXISTING=$(crontab -l 2>/dev/null | grep -v "$SCRIPT_PATH")

if [ -n "$EXISTING" ]; then
    echo "$EXISTING" | crontab -
fi

echo "$CRON_CMD" | crontab -

echo "Cron job installed: runs every 10 minutes"
echo "Command: $SCRIPT_PATH"
crontab -l
