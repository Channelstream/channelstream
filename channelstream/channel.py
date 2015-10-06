import gevent
import copy
import logging

from channelstream import lock
from channelstream.connection import connections
from channelstream.user import users
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

channels = {}


class Channel(object):
    """ Represents one of our chat channels - has some config options """

    def __init__(self, name, long_name=None, channel_configs=None):
        self.name = name
        self.long_name = long_name
        self.last_active = datetime.utcnow()
        self.connections = {}
        self.notify_presence = False
        self.salvageable = False
        self.store_history = False
        self.history_size = 10
        self.history = []
        self.reconfigure_from_dict(channel_configs.get(self.name))
        log.info('%s created' % self)

    def reconfigure_from_dict(self, config):
        if config:
            keys = ['notify_presence', 'store_history', 'history_size']
            for key in keys:
                val = config.get(key)
                if val is not None:
                    setattr(self, key, val)

    def add_connection(self, connection):
        if connection.username not in self.connections:
            self.connections[connection.username] = []
        if not self.connections[connection.username] and self.notify_presence:
            self.send_notify_presence_info(connection.username, 'joined')

        if connection not in self.connections[connection.username]:
            self.connections[connection.username].append(connection)

    def send_notify_presence_info(self, username, action):
        self.last_active = datetime.utcnow()
        payload = {
            'type': 'presence',
            'user': username,
            'channel': self.name,
            'message': {'action': action}
        }
        self.add_message(payload, exclude_users=username)

    def add_message(self, message, pm_users=None, exclude_users=None):
        """ Sends the message to all connections subscribed to this channel """
        message = copy.deepcopy(message)
        if not pm_users:
            pm_users = []
        self.last_active = datetime.utcnow()
        if self.store_history:
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
        for channel in channels.itervalues():
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
            if conn.username in users:
                if conn in users[conn.username].connections:
                    users[conn.username].connections.remove(conn)
            if conn.id in connections:
                del connections[conn.id]
            # make sure connection is closed after we garbage collected it from our list
            if conn.socket:
                try:
                    conn.socket.ws.close()
                except Exception:
                    raise
        log.debug('gc_conns() time %s' % (datetime.utcnow() - start_time))
        gevent.spawn_later(1, gc_conns)


gevent.spawn_later(1, gc_conns)
