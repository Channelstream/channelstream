import logging

import six

from channelstream import server_state
from channelstream.user import User
from channelstream.connection import Connection
from channelstream.channel import Channel

log = logging.getLogger(__name__)


def connect(
    username=None,
    fresh_user_state=None,
    state_public_keys=None,
    update_user_state=None,
    conn_id=None,
    channels=None,
    channel_configs=None,
):
    """

    :param username:
    :param fresh_user_state:
    :param state_public_keys:
    :param update_user_state:
    :param conn_id:
    :param channels:
    :param channel_configs:
    :return:
    """
    with server_state.lock:
        if username not in server_state.USERS:
            user = User(username)
            user.state_from_dict(fresh_user_state)
            server_state.USERS[username] = user
        else:
            user = server_state.USERS[username]
        if state_public_keys is not None:
            user.state_public_keys = state_public_keys

        user.state_from_dict(update_user_state)
        connection = Connection(username, conn_id)
        if connection.id not in server_state.CONNECTIONS:
            server_state.CONNECTIONS[connection.id] = connection
        user.add_connection(connection)
        for channel_name in channels:
            # user gets assigned to a channel
            if channel_name not in server_state.CHANNELS:
                channel = Channel(
                    channel_name, channel_config=channel_configs.get(channel_name)
                )
                server_state.CHANNELS[channel_name] = channel
            server_state.CHANNELS[channel_name].add_connection(connection)
        log.info("connecting %s with uuid %s" % (username, connection.id))
        return connection, user


def subscribe(connection=None, channels=None, channel_configs=None):
    """

    :param connection:
    :param channels:
    :param channel_configs:
    :return:
    """
    user = server_state.USERS.get(connection.username)
    subscribed_to = []
    with server_state.lock:
        if user:
            for channel_name in channels:
                if channel_name not in server_state.CHANNELS:
                    channel = Channel(
                        channel_name, channel_config=channel_configs.get(channel_name)
                    )
                    server_state.CHANNELS[channel_name] = channel
                is_found = server_state.CHANNELS[channel_name].add_connection(
                    connection
                )
                if is_found:
                    subscribed_to.append(channel_name)
    return subscribed_to


def unsubscribe(connection=None, unsubscribe_channels=None):
    """

    :param connection:
    :param unsubscribe_channels:
    :return:
    """
    user = server_state.USERS.get(connection.username)
    unsubscribed_from = []
    with server_state.lock:
        if user:
            for channel_name in unsubscribe_channels:
                if channel_name in server_state.CHANNELS:
                    is_found = server_state.CHANNELS[channel_name].remove_connection(
                        connection
                    )
                    if is_found:
                        unsubscribed_from.append(channel_name)
    return unsubscribed_from


def change_user_state(user_inst=None, user_state=None):
    """

    :param user_inst:
    :param user_state:
    :return:
    """
    changed = user_inst.state_from_dict(user_state)
    # mark active
    user_inst.mark_activity()
    if changed:
        channels = user_inst.get_channels()
        for channel in [c for c in channels if c.notify_state]:
            channel.send_user_state(user_inst, changed)
    return changed


def disconnect(conn_id):
    """

    :param conn_id:
    :return:
    """
    conn = server_state.CONNECTIONS.get(conn_id)
    if conn is not None:
        conn.mark_for_gc()
        return True
    return False


def set_channel_config(channel_configs):
    """

    :param channel_configs:
    :return:
    """
    with server_state.lock:
        for channel_name, config in channel_configs.items():
            if not server_state.CHANNELS.get(channel_name):
                channel = Channel(
                    channel_name, channel_config=channel_configs.get(channel_name)
                )
                server_state.CHANNELS[channel_name] = channel
            else:
                channel = server_state.CHANNELS[channel_name]
                channel.reconfigure_from_dict(channel_configs.get(channel_name))


def pass_message(msg, stats):
    """

    :param msg:
    :param stats:
    :return:
    """

    msg["catchup"] = False
    msg["edited"] = None
    msg["type"] = "message"

    total_sent = 0
    stats["total_unique_messages"] += 1
    if msg.get("channel"):
        channel_inst = server_state.CHANNELS.get(msg["channel"])
        if channel_inst:
            total_sent += channel_inst.add_message(
                msg, pm_users=msg["pm_users"], exclude_users=msg["exclude_users"]
            )
    elif msg["pm_users"]:
        # if pm then iterate over all users and notify about new message!
        for username in msg["pm_users"]:
            user_inst = server_state.USERS.get(username)
            if user_inst:
                total_sent += user_inst.add_message(msg)
    stats["total_messages"] += total_sent


def edit_message(msg):
    """

    :param msg:
    :param stats:
    :return:
    """

    # this will be computationally heavy, but at same time edits do not happen often
    for channel_inst in six.itervalues(server_state.CHANNELS):
        channel_inst.alter_message(msg)

    for user_inst in six.itervalues(server_state.USERS):
        user_inst.alter_message(msg)
