#!/bin/sh
# Check if backup service is healthy

# Check if last backup was successful (within 25 hours)
LAST_BACKUP_FILE="/var/lib/node_exporter/textfile_collector/backup.prom"
if [ -f "$LAST_BACKUP_FILE" ]; then
    LAST_RUN=$(grep "backup_last_run_timestamp" "$LAST_BACKUP_FILE" | awk '{print $2}')
    CURRENT_TIME=$(date +%s)
    TIME_DIFF=$((CURRENT_TIME - LAST_RUN))
    
    # If last backup was more than 25 hours ago, unhealthy
    if [ $TIME_DIFF -gt 90000 ]; then
        exit 1
    fi
else
    # No backup file yet, check if service just started
    UPTIME=$(awk '{print int($1)}' /proc/uptime)
    if [ $UPTIME -gt 3600 ]; then
        # Running for more than an hour without backup file
        exit 1
    fi
fi

exit 0
