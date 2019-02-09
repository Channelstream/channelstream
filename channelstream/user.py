import copy
import logging
import uuid
from datetime import datetime

from channelstream.server_state import get_state
from channelstream.utils import process_catchup
from channelstream.validation import MSG_EDITABLE_KEYS

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
        # those frames will store private messages
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
        message = copy.deepcopy(message)
        message.pop("no_history", None)
        message.pop("pm_users", None)
        message.pop("exclude_users", None)
        self.add_frame(message)
        self.mark_activity()
        for connection in self.connections:
            connection.add_message(message)
        return len(self.connections)

    def state_from_dict(self, state_dict):
        changed = []
        if isinstance(state_dict, dict):
            for k, v in state_dict.items():
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
        server_state = get_state()
        channels = []
        for channel in server_state.channels.values():
            if channel.connections.get(self.username):
                channels.append(channel)
        return channels

    def alter_message(self, to_edit):
        # normally tried to get channel and user from history
        for f, msg in self.frames:
            if msg["uuid"] == to_edit["uuid"] and msg["type"] == "message":
                msg.update({k: v for k, v in to_edit.items() if k in MSG_EDITABLE_KEYS})
                break
        altered = copy.deepcopy(to_edit)
        altered["type"] = "message:edit"
        self.add_message(altered)

    def delete_message(self, to_delete):
        # normally tried to get channel and user from history
        for i, frame in enumerate(self.frames):
            msg = frame[1]
            if msg["uuid"] == to_delete["uuid"] and msg["type"] == "message":
                self.frames.pop(i)
                break

        deleted = copy.deepcopy(to_delete)
        deleted["type"] = "message:delete"
        self.add_message(deleted)

    def __json__(self, request=None):
        return self.get_info()
