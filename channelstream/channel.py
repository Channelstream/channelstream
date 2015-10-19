import copy
import gevent
import logging
import uuid

from . import lock
from .connection import CONNECTIONS
from .user import USERS
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

CHANNELS = {}


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
        self.reconfigure_from_dict(channel_configs.get(self.name))
        log.info('%s created' % self)

    def reconfigure_from_dict(self, config):
        if config:
            keys = ['notify_presence', 'store_history', 'history_size',
                    'broadcast_presence_with_user_lists']
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

        if not self.connections[username] and self.notify_presence:
            self.send_notify_presence_info(username, 'parted')

        self.connections[username] = filter(lambda i: i is not connection,
                                            self.connections[username])

    def send_notify_presence_info(self, username, action):
        """
        Sends a message to other connected parties about a presence change
        """
        connected_users = []
        if self.broadcast_presence_with_user_lists:
            for _username in self.connections.keys():
                user_inst = USERS.get(_username)
                udata = {
                    'user': user_inst.username,
                    'state': user_inst.public_state
                }
                connected_users.append(udata)

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

    def add_message(self, message, pm_users=None, exclude_users=None):
        """
        Sends the message to all connections subscribed to this channel
        """
        message = copy.deepcopy(message)
        if not pm_users:
            pm_users = []
        self.last_active = datetime.utcnow()
        if self.store_history and message['type'] == 'message':
            self.history.append(message)
            self.history = self.history[(self.history_size) * -1:]
        message.update({'channel': self.name})
        # message everyone subscribed except excluded
        total_sent = 0
        for u, conns in self.connections.iteritems():
            if not exclude_users or u not in exclude_users:
                for connection in conns:
                    if not pm_users or connection.user in pm_users:
                        connection.add_message(message)
                        total_sent += 1
        return total_sent

    def __repr__(self):
        return '<Channel: %s, connections:%s>' % (
            self.name, len(self.connections))


def gc_conns():
    with lock:
        start_time = datetime.utcnow()
        threshold = start_time - timedelta(seconds=15)
        collected_conns = []
        # collect every ref in chanels
        for channel in CHANNELS.itervalues():
            for username, conns in channel.connections.items():
                for conn in conns:
                    if conn.last_active < threshold:
                        channel.connections[username].remove(conn)
                        collected_conns.append(conn)
                if not channel.connections[username]:
                    del channel.connections[username]
                    channel.send_notify_presence_info(username, 'parted')
        # remove old conns from users and conn dict
        for conn in collected_conns:
            if conn.username in USERS:
                if conn in USERS[conn.username].connections:
                    USERS[conn.username].connections.remove(conn)
            if conn.id in CONNECTIONS:
                del CONNECTIONS[conn.id]
            # make sure connection is closed after we garbage
            # collected it from our list
            if conn.socket:
                try:
                    conn.socket.ws.close()
                except Exception:
                    raise
        log.debug('gc_conns() time %s' % (datetime.utcnow() - start_time))
        gevent.spawn_later(1, gc_conns)


gevent.spawn_later(1, gc_conns)
