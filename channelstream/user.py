from datetime import datetime, timedelta
from channelstream import lock
import logging

import gevent

log = logging.getLogger(__name__)

users = {}


class User(object):
    """ represents a unique user of the system """

    def __init__(self, username, status):
        self.username = username
        self.status = status
        self.connections = []  # holds ids of connections
        self.last_active = datetime.utcnow()

    def __repr__(self):
        return '<User:%s, status:%s, connections:%s>' % (
            self.username, self.status, len(self.connections))

    def add_connection(self, connection):
        """ creates a new connection for user"""
        if connection not in self.connections:
            self.connections.append(connection)
        # mark active
        self.last_active = datetime.utcnow()
        return connection

    def add_message(self, message):
        """ Send a message to all connections of this user """
        # mark active
        self.last_active = datetime.utcnow()
        for connection in self.connections:
            connection.add_message(message)
        return len(self.connections)


def gc_users():
    with lock:
        start_time = datetime.utcnow()
        threshold = datetime.utcnow() - timedelta(days=1)
        for user in users.values():
            if user.last_active < threshold:
                users.pop(user.username)
        log.info('gc_users() time %s' % (datetime.utcnow() - start_time))
    gevent.spawn_later(60, gc_users)


gevent.spawn_later(60, gc_users)
