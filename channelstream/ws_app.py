from six.moves.urllib.parse import parse_qs

from ws4py.websocket import WebSocket

from channelstream import server_state


class ChatApplicationSocket(WebSocket):
    def opened(self):
        self.qs = parse_qs(self.environ["QUERY_STRING"])
        self.conn_id = self.qs.get("conn_id", "-")[0]
        if self.conn_id not in server_state.CONNECTIONS:
            # close connection instantly if user played with id
            self.close()
        else:
            # attach a socket to connection
            connection = server_state.CONNECTIONS[self.conn_id]
            connection.socket = self
            connection.deliver_catchup_messages()

    def received_message(self, m):
        # this is to allow client heartbeats
        if self.conn_id in server_state.CONNECTIONS:
            connection = server_state.CONNECTIONS[self.conn_id]
            connection.mark_activity()
            user = server_state.USERS.get(connection.username)
            if user:
                user.mark_activity()

    def closed(self, code, reason=""):
        self.environ.pop("ws4py.app")
        found_conn = self.conn_id in server_state.CONNECTIONS
        if hasattr(self, "conn_id") and found_conn:
            connection = server_state.CONNECTIONS[self.conn_id]
            connection.mark_for_gc()
