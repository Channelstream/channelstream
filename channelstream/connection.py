import logging
from datetime import datetime, timedelta

import gevent

import channelstream
from .ext_json import json

log = logging.getLogger(__name__)


class Connection(object):
    """ Represents a browser connection"""

    def __init__(self, username, conn_id):
        self.username = username  # hold user id/name of connection
        self.last_active = datetime.utcnow()
        self.socket = None
        self.queue = None
        self.id = conn_id
        gevent.spawn_later(5, self.heartbeat)

    def __repr__(self):
        return '<Connection: id:%s, owner:%s>' % (self.id, self.username)

    def add_message(self, message=None):
        """ Sends the message to the client connection """
        # handle websockets
        if self.socket and self.socket.terminated:
            self.mark_for_gc()
        elif self.socket and not self.socket.terminated:
            try:
                # payload needs to be converted to JSON now as it gets
                # piped to client
                self.socket.send(json.dumps([message] if message else []))
                now = datetime.utcnow()
                self.last_active = now
                channelstream.USERS[self.username].last_active = now
            except Exception:
                self.mark_for_gc()
        elif self.queue:
            # handle long polling
            # payload will be converted to JSON in WSGI response
            self.queue.put([message] if message else [])

    def mark_for_gc(self):
        # set last active time for connection 1 hour in past for GC
        self.last_active -= timedelta(days=60)

    def heartbeat(self):
        if self.socket or self.queue:
            try:
                self.add_message()
                gevent.spawn_later(5, self.heartbeat)
            except Exception:
                self.mark_for_gc()
                if self.socket:
                    self.socket.close()

    def __json__(self):
        return self.id