import logging
import gevent

from datetime import datetime, timedelta
from . import lock


log = logging.getLogger(__name__)

USERS = {}


class User(object):
    """ represents a unique user of the system """

    def __init__(self, username):
        self.username = username
        self.state = {}
        self.state_public_keys = []
        self.connections = []  # holds ids of connections
        self.last_active = datetime.utcnow()

    def __repr__(self):
        return '<User:%s, connections:%s>' % (
            self.username, len(self.connections))

    def add_connection(self, connection):
        """
        creates a new connection for user
        """
        if connection not in self.connections:
            self.connections.append(connection)
        # mark active
        self.last_active = datetime.utcnow()
        return connection

    def add_message(self, message):
        """
        Send a message to all connections of this user
        """
        # mark active
        self.last_active = datetime.utcnow()
        for connection in self.connections:
            connection.add_message(message)
        return len(self.connections)

    def state_from_dict(self, state_dict):
        if isinstance(state_dict, dict):
            self.state.update(state_dict)

    @property
    def public_state(self):
        return dict([(k, v) for k, v in self.state.items()
                     if k in self.state_public_keys])

def gc_users():
    with lock:
        start_time = datetime.utcnow()
        threshold = datetime.utcnow() - timedelta(days=1)
        for user in USERS.values():
            if user.last_active < threshold:
                USERS.pop(user.username)
        log.info('gc_users() time %s' % (datetime.utcnow() - start_time))
    gevent.spawn_later(60, gc_users)


gevent.spawn_later(60, gc_users)
