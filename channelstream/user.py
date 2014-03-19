from datetime import datetime, timedelta
import logging

import gevent


log = logging.getLogger(__name__)

users ={}

class User(object):
    """ represents a unique user of the system """

    def __init__(self, user_name, status):
        self.user_name = user_name
        self.status = status
        self.connections = []  # holds ids of connections
        self.last_active = datetime.utcnow()

    def __repr__(self):
        return '<User:%s, status:%s, connections:%s>' % (
        self.user_name, self.status, len(self.connections))

    def add_connection(self, connection):
        """ creates a new connection for user"""
        if connection not in self.connections:
            self.connections.append(connection)
        # mark active
        self.last_active = datetime.utcnow()
        return connection

    def add_message(self, message):
        # mark active
        self.last_active = datetime.utcnow()
        for connection in self.connections:
            connection.add_message(message)
        return len(self.connections)


def gc_users():
    while True:
        gevent.sleep(60)
        start_time = datetime.utcnow()
        threshold = datetime.utcnow() - timedelta(days=1)
        for user in users.values():
            if user.last_active < threshold:
                users.pop(user.user_name)
        log.info('gc_users() time %s' % (datetime.utcnow() - start_time))

gevent.spawn(gc_users)