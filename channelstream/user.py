import logging
import uuid

from datetime import datetime

import six
from channelstream import server_state
from channelstream.utils import process_catchup

log = logging.getLogger(__name__)


class User(object):
    """ represents a unique user of the system """

    def __init__(self, username):
        self.uuid = uuid.uuid4()
        self.username = username
        self.state = {}
        self.state_public_keys = []
        self.connections = []  # holds ids of connections
        # store frames for fetching when connection is established
        self.frames = []
        self.last_active = None
        self.mark_activity()

    def mark_activity(self):
        self.last_active = datetime.utcnow()

    def __repr__(self):
        return "<User:%s, connections:%s>" % (self.username, len(self.connections))

    def add_frame(self, frame):
        self.frames.append((datetime.utcnow(), frame))
        self.frames = self.frames[-50:]

    def get_catchup_frames(self, newer_than):
        return [process_catchup(f[1]) for f in self.frames if f[0] > newer_than]

    def add_connection(self, connection):
        """
        creates a new connection for user
        """
        if connection not in self.connections:
            self.connections.append(connection)
        # mark active
        self.mark_activity()
        return connection

    def add_message(self, message):
        """
        Send a message to all connections of this user
        """
        # mark active
        self.add_frame(message)
        self.mark_activity()
        for connection in self.connections:
            connection.add_message(message)
        return len(self.connections)

    def state_from_dict(self, state_dict):
        changed = []
        if isinstance(state_dict, dict):
            for k, v in six.iteritems(state_dict):
                if self.state.get(k) != v:
                    self.state[k] = v
                    changed.append({"key": k, "value": v})
        return changed

    @property
    def public_state(self):
        return {k: v for k, v in self.state.items() if k in self.state_public_keys}

    def get_info(self, include_connections=False):
        info = {"state": self.public_state, "user": self.username, "uuid": self.uuid}
        if include_connections:
            info["connections"] = [c.id for c in self.connections]
        return info

    def get_channels(self):
        channels = []
        for channel in six.itervalues(server_state.CHANNELS):
            if channel.connections.get(self.username):
                channels.append(channel)
        return channels

    def __json__(self, request=None):
        return self.get_info()
