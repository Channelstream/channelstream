import logging
from datetime import datetime, timedelta

import gevent

from channelstream import patched_json as json
from channelstream.server_state import get_state

log = logging.getLogger(__name__)


class Connection(object):
    """ Represents a client connection"""

    def __init__(self, username, conn_id):
        self.username = username  # hold user id/name of connection
        self.last_active = None
        self.socket = None
        self.queue = None
        self.id = conn_id
        self.mark_activity()
        gevent.spawn_later(5, self.heartbeat_forever)

    def __repr__(self):
        return "<Connection: id:%s, owner:%s>" % (self.id, self.username)

    def mark_activity(self):
        self.last_active = datetime.utcnow()

    def add_message(self, message=None):
        server_state = get_state()
        """ Sends the message to the client connection """
        # handle websockets
        if self.socket and self.socket.terminated:
            self.mark_for_gc()
        elif self.socket and not self.socket.terminated:
            try:
                # payload needs to be converted to JSON now as it gets
                # piped to client
                self.socket.send(json.dumps([message] if message else []))
                self.mark_activity()
                server_state.users[self.username].mark_activity()
            except Exception as exc:
                log.info(exc)
                self.mark_for_gc()
        elif self.queue:
            # handle long polling
            # payload will be converted to JSON in WSGI response
            self.queue.put([message] if message else [])

    def mark_for_gc(self):
        # set last active time for connection 1 hour in past for GC
        self.last_active -= timedelta(days=60)

    def heartbeat(self):
        if (self.socket and not self.socket.terminated) or self.queue:
            try:
                self.add_message()
                return True
            except Exception as exc:
                self.mark_for_gc()
                if self.socket:
                    self.socket.close()

    def heartbeat_forever(self):
        while True:
            if self.heartbeat():
                gevent.sleep(5)
            else:
                break

    def get_catchup_messages(self):
        server_state = get_state()
        messages = []
        # return catchup messages for channels
        for channel in self.channels:
            channel_inst = server_state.channels[channel]
            messages.extend(
                channel_inst.get_catchup_frames(self.last_active, self.username)
            )
        # and users
        messages.extend(
            server_state.users[self.username].get_catchup_frames(self.last_active)
        )
        return messages

    def deliver_catchup_messages(self):
        [self.add_message(m) for m in self.get_catchup_messages()]

    @property
    def channels(self):
        """
        Return list of channels names connection belongs to
        :return:
        """
        server_state = get_state()
        found_channels = []
        for channel in server_state.channels.values():
            user_conns = channel.connections.get(self.username) or []
            if self in user_conns:
                found_channels.append(channel.name)
        return sorted(found_channels)

    def __json__(self):
        return self.id
