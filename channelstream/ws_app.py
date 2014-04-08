from datetime import datetime
import urlparse

from geventwebsocket import WebSocketApplication

from channelstream import lock
from channelstream.connection import connections
from channelstream.channel import channels
from channelstream.user import users


class ChatApplication(WebSocketApplication):
    def on_open(self):
        self.qs = urlparse.parse_qs(self.ws.environ['QUERY_STRING'])
        self.conn_id = self.qs['conn_id'][0]
        if self.conn_id not in connections:
            # close connection instantly if user played with id
            self.ws.close()
        else:
            # attach a socket to connection
            connections[self.conn_id].socket = self


    def on_message(self, message):
        # this is to allow client heartbeats
        now = datetime.utcnow()
        if self.conn_id in connections:
            connection = connections[self.conn_id]
            connection.last_active = now
            user = users.get(connection.username)
            if user:
                user.last_active = now


    def on_close(self, reason):
        if hasattr(self, 'conn_id') and self.conn_id in connections:
            connection = connections[self.conn_id]
            with lock:
                if connection.username in users:
                    # remove conn id instance from user
                    users[connection.username].connections.remove(connection)
                # remove from channel
                for channel in channels.itervalues():
                    if connection.username in channel.connections:
                        channel.connections[connection.username].remove(connection)
                # remove from conections
                del connections[self.conn_id]