#!/bin/bash

# Cron runs with a bare environment — it won't see vars injected via --env-file.
# Dumping the current environment to /etc/environment makes them available to all cron jobs.
printenv >> /etc/environment

exec cron -f
