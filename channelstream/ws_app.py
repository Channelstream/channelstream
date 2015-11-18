import urlparse
from datetime import datetime

from geventwebsocket import WebSocketApplication

import channelstream


class ChatApplication(WebSocketApplication):
    def on_open(self):
        self.qs = urlparse.parse_qs(self.ws.environ['QUERY_STRING'])
        self.conn_id = self.qs['conn_id'][0]
        if self.conn_id not in channelstream.CONNECTIONS:
            # close connection instantly if user played with id
            self.ws.close()
        else:
            # attach a socket to connection
            channelstream.CONNECTIONS[self.conn_id].socket = self

    def on_message(self, message):
        # this is to allow client heartbeats
        now = datetime.utcnow()
        if self.conn_id in channelstream.CONNECTIONS:
            connection = channelstream.CONNECTIONS[self.conn_id]
            connection.last_active = now
            user = channelstream.USERS.get(connection.username)
            if user:
                user.last_active = now

    def on_close(self, reason):
        found_conn = self.conn_id in channelstream.CONNECTIONS
        if hasattr(self, 'conn_id') and found_conn:
            connection = channelstream.CONNECTIONS[self.conn_id]
            # set activity date in past to salvage
            connection.last_active = datetime(1980, 1, 1)
