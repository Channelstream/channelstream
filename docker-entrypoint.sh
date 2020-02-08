#!/bin/bash
set -e
# create config file if it doesn't exist in the config volume
if [ ! -f /channelstream/config/channelstream_config.ini ]; then
    echo "Creating configuration file"
    env/bin/channelstream_utils make_config -o /channelstream/config/channelstream_config.ini
fi;

exec env/bin/channelstream -i /channelstream/config/channelstream_config.ini
