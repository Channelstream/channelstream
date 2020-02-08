#!/bin/bash
set -e
# create config file if it doesn't exist in the config volume
if [ ! -f /channelstream/config/channelstream_config.ini ]; then
    echo "Creating fresh configuration file"
    channelstream_utils make_config -o /channelstream/config/channelstream_config.ini
fi;

exec "$@"
