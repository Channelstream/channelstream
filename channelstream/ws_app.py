from six.moves.urllib.parse import parse_qs
from datetime import datetime

from ws4py.websocket import WebSocket

import channelstream


class ChatApplicationSocket(WebSocket):
    def opened(self):
        self.qs = parse_qs(self.environ['QUERY_STRING'])
        self.conn_id = self.qs.get('conn_id', '-')[0]
        if self.conn_id not in channelstream.CONNECTIONS:
            # close connection instantly if user played with id
            self.close()
        else:
            # attach a socket to connection
            channelstream.CONNECTIONS[self.conn_id].socket = self

    def received_message(self, m):
        # this is to allow client heartbeats
        now = datetime.utcnow()
        if self.conn_id in channelstream.CONNECTIONS:
            connection = channelstream.CONNECTIONS[self.conn_id]
            connection.last_active = now
            user = channelstream.USERS.get(connection.username)
            if user:
                user.last_active = now

    def closed(self, code, reason=""):
        self.environ.pop('ws4py.app')
        found_conn = self.conn_id in channelstream.CONNECTIONS
        if hasattr(self, 'conn_id') and found_conn:
            connection = channelstream.CONNECTIONS[self.conn_id]
            connection.mark_for_gc()
