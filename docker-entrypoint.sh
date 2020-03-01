#!/bin/bash
set -e
# create config file if it doesn't exist in the config volume
if [ ! -f /opt/application/rundir/config.ini ]; then
    echo "Creating fresh configuration file"
    channelstream_utils make_config -o /opt/application/rundir/config.ini
fi;

exec "$@"
