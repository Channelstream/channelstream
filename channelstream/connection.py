import datetime
import gevent
import logging

from gevent.queue import Queue

from channelstream.ext_json import json

log = logging.getLogger(__name__)

connections = {}


class Connection(object):
    """ Represents a browser connection"""

    def __init__(self, username, conn_id):
        self.username = username  # hold user id/name of connection
        self.last_active = datetime.datetime.utcnow()
        self.socket = None
        self.queue = None
        self.id = conn_id
        gevent.spawn_later(5, self.heartbeat)

    def __repr__(self):
        return '<Connection: id:%s, owner:%s>' % (self.id, self.username)

    def add_message(self, message=None):
        """ Sends the message to the client connection """
        # handle websockets
        if self.socket:
            if message:
                self.socket.ws.send(json.dumps([message]))
            else:
                self.socket.ws.send(json.dumps([]))
            self.last_active = datetime.datetime.utcnow()
        elif self.queue:
            # handle long polling
            if message:
                self.queue.put([message])
            else:
                self.queue.put([])

    def mark_for_gc(self):
        # set last active time for connection 1 hour in past for GC
        self.last_active -= datetime.timedelta(minutes=60)

    def heartbeat(self):
        if self.socket or self.queue:
            try:
                self.add_message()
                gevent.spawn_later(5, self.heartbeat)
            except Exception as e:
                self.mark_for_gc()
                if self.socket:
                    self.socket.ws.close()
