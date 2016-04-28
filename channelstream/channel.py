import copy
import logging
import six
import uuid

from datetime import datetime

import channelstream

log = logging.getLogger(__name__)


class Channel(object):
    """ Represents one of our chat channels - has some config options """

    def __init__(self, name, long_name=None, channel_configs=None):
        self.name = name
        self.long_name = long_name
        self.last_active = datetime.utcnow()
        self.connections = {}
        self.notify_presence = False
        self.broadcast_presence_with_user_lists = False
        self.salvageable = False
        self.store_history = False
        self.history_size = 10
        self.history = []
        if not channel_configs:
            channel_configs = {}
        self.reconfigure_from_dict(channel_configs.get(self.name))
        log.info('%s created' % self)

    def reconfigure_from_dict(self, config):
        if config:
            keys = ('notify_presence', 'store_history', 'history_size',
                    'broadcast_presence_with_user_lists')
            for key in keys:
                val = config.get(key)
                if val is not None:
                    setattr(self, key, val)

    def add_connection(self, connection):
        username = connection.username
        if username not in self.connections:
            self.connections[username] = []

        if not self.connections[username] and self.notify_presence:
            self.send_notify_presence_info(username, 'joined')

        if connection not in self.connections[connection.username]:
            self.connections[connection.username].append(connection)

    def remove_connection(self, connection):
        username = connection.username
        if username not in self.connections:
            self.connections[username] = []

        if connection in self.connections[username]:
            self.connections[username].remove(connection)

        self.after_parted(username)

    def after_parted(self, username):
        """
        Sends parted message if necessary and removed username from
        connections if empty

        :param username:
        :return:
        """
        if not self.connections[username]:
            del self.connections[username]
            if self.notify_presence:
                self.send_notify_presence_info(username, 'parted')

    def send_notify_presence_info(self, username, action):
        """
        Sends a message to other connected parties about a presence change
        :param username:
        :param action:
        :return:
        """
        connected_users = []
        if self.broadcast_presence_with_user_lists:
            for _username in self.connections.keys():
                user_inst = channelstream.USERS.get(_username)
                user_data = {
                    'user': user_inst.username,
                    'state': user_inst.public_state
                }
                connected_users.append(user_data)

        self.last_active = datetime.utcnow()
        payload = {
            'uuid': str(uuid.uuid4()).replace('-', ''),
            'type': 'presence',
            'user': username,
            'users': connected_users,
            'timestamp': self.last_active,
            'channel': self.name,
            'message': {'action': action}
        }
        self.add_message(payload, exclude_users=username)
        return payload

    def add_message(self, message, pm_users=None, exclude_users=None):
        """
        Sends the message to all connections subscribed to this channel
        """
        message = copy.deepcopy(message)
        pm_users = pm_users or []
        self.last_active = datetime.utcnow()
        if self.store_history and message['type'] == 'message':
            self.history.append(message)
            self.history = self.history[(self.history_size) * -1:]
        message.update({'channel': self.name})
        # message everyone subscribed except excluded
        total_sent = 0
        for user, conns in six.iteritems(self.connections):
            if not exclude_users or user not in exclude_users:
                for connection in conns:
                    if not pm_users or connection.user in pm_users:
                        connection.add_message(message)
                        total_sent += 1
        return total_sent

    def __repr__(self):
        return '<Channel: %s, connections:%s>' % (
            self.name, len(self.connections))
