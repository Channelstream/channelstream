from urllib.parse import parse_qs
from ws4py.websocket import WebSocket

from channelstream import utils
from channelstream.server_state import get_state


class ChatApplicationSocket(WebSocket):
    def __init__(self, *args, **kwargs):
        super(ChatApplicationSocket, self).__init__(*args, **kwargs)
        self.qs = None
        self.conn_id = None

    def opened(self):
        server_state = get_state()
        self.qs = parse_qs(self.environ["QUERY_STRING"])
        self.conn_id = utils.uuid_from_string(self.qs.get("conn_id")[0])
        if self.conn_id not in server_state.connections:
            # close connection instantly if user played with id
            self.close()
        else:
            # attach a socket to connection
            connection = server_state.connections[self.conn_id]
            connection.socket = self
            connection.deliver_catchup_messages()

    def received_message(self, m):
        server_state = get_state()
        # this is to allow client heartbeats
        if self.conn_id in server_state.connections:
            connection = server_state.connections[self.conn_id]
            connection.mark_activity()
            user = server_state.users.get(connection.username)
            if user:
                user.mark_activity()

    def closed(self, code, reason=""):
        server_state = get_state()
        self.environ.pop("ws4py.app")
        found_conn = self.conn_id in server_state.connections
        if hasattr(self, "conn_id") and found_conn:
            connection = server_state.connections[self.conn_id]
            connection.mark_for_gc()
