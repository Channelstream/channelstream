#!/bin/bash
set -e

# change the app uid to ones set from environment
if [ -n "${USER_UID}" ]; then
  usermod -u $USER_UID application
fi
if [ -n "${USER_GID}" ]; then
  groupmod -g $USER_GID application
fi

# create config file if it doesn't exist in the config volume
if [ ! -f /opt/application/rundir/config.ini ]; then
    echo "Creating fresh configuration file"
    gosu application channelstream_utils make_config -o /opt/application/rundir/config.ini
fi;

gosu application "$@"
