from datetime import datetime, timedelta
import logging

import gevent

from channelstream.connection import connections
from channelstream.user import users


log = logging.getLogger(__name__)

channels = {}

class Channel(object):
    """ Represents one of our chat channels - has some config options """

    def __init__(self, name, long_name=None):
        self.name = name
        self.long_name = long_name
        self.last_active = datetime.utcnow()
        self.connections = {}
        self.presence = False
        self.salvagable = False
        self.store_history = False
        self.history_size = 10
        self.history = []
        log.info('%s created' % self)

    def add_connection(self, connection):
        if not connection.user_name in self.connections:
            self.connections[connection.user_name] = []
        if connection not in self.connections[connection.user_name]:
            self.connections[connection.user_name].append(connection)

    def add_message(self, message, pm_users=None, exclude_user=None):
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
            if u != exclude_user:
                for connection in conns:
                    if not pm_users or connection.user in pm_users:
                        connection.add_message(message)
                        total_sent += 1
        return total_sent

    def __repr__(self):
        return '<Channel: %s, connections:%s>' % (
            self.name, len(self.connections))


def gc_conns():
    while True:
        gevent.sleep(5)
        start_time = datetime.utcnow()
        threshold = start_time - timedelta(seconds=15)
        collected_conns = []
        # collect every ref in chanels
        for channel in channels.itervalues():
            for k, conns in channel.connections.items():
                for conn in conns:
                    if conn.last_active < threshold:
                        channel.connections[k].remove(conn)
                        collected_conns.append(conn)
                if not channel.connections[k]:
                    del channel.connections[k]
        # remove old conns from users and conn dict
        for conn in collected_conns:
            if conn.user_name in users:
                if conn in users[conn.user_name].connections:
                    users[conn.user_name].connections.remove(conn)
            if conn.id in connections:
                del connections[conn.id]
            # make sure connection is closed after we garbage collected it from our list
            if conn.socket:
                conn.socket.ws.close()
        log.info('gc_conns() time %s' % (datetime.utcnow() - start_time))

gevent.spawn(gc_conns)