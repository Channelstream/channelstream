from gevent import monkey

monkey.patch_all()

import pytest
from datetime import datetime, timedelta
from gevent.queue import Queue
from channelstream.server_state import get_state
import channelstream.gc
from channelstream.channel import Channel
from channelstream.connection import Connection
from channelstream.user import User


@pytest.mark.usefixtures("cleanup_globals", "test_uuids")
class TestChannel(object):
    def test_create_defaults(self):
        channel = Channel("test", long_name="long name")
        assert channel.name == "test"
        assert channel.long_name == "long name"
        assert channel.connections == {}
        assert channel.notify_presence is False
        assert channel.broadcast_presence_with_user_lists is False
        assert channel.salvageable is False
        assert channel.store_history is False
        assert channel.history_size == 10
        assert channel.history == []

    def test_repr(self):
        channel = Channel("test", long_name="long name")
        assert repr(channel) == "<Channel: test, connections:0>"

    @pytest.mark.parametrize(
        "prop, value",
        [
            ("notify_presence", True),
            ("store_history", 6),
            ("history_size", 42),
            ("broadcast_presence_with_user_lists", True),
        ],
    )
    def test_create_set_config(self, prop, value):
        channel_config = {prop: value}
        channel = Channel("test", channel_config=channel_config)

        assert getattr(channel, prop) == value

    def test_add_connection(self, test_uuids):
        connection = Connection("test_user", conn_id=test_uuids[1])
        channel = Channel("test")
        channel.add_connection(connection)
        assert len(channel.connections["test_user"]) == 1
        assert "test_user" in channel.connections
        assert connection in channel.connections["test_user"]
        assert repr(channel) == "<Channel: test, connections:1>"

    def test_remove_connection(self, test_uuids):
        connection = Connection("test_user", conn_id=test_uuids[1])
        connection2 = Connection("test_user2", conn_id=test_uuids[2])
        connection3 = Connection("test_user", conn_id=test_uuids[3])
        channel = Channel("test")
        channel.add_connection(connection)
        channel.add_connection(connection2)
        channel.remove_connection(connection)
        assert "test_user" not in channel.connections
        assert len(channel.connections["test_user2"]) == 1
        channel.add_connection(connection)
        channel.add_connection(connection3)
        channel.remove_connection(connection)
        assert len(channel.connections["test_user"]) == 1

    def test_remove_non_existant_connection(self, test_uuids):
        channel = Channel("test")
        connection = Connection("test_user", conn_id=test_uuids[1])
        channel.remove_connection(connection)
        assert "test_user" not in channel.connections

    def test_remove_connection_w_presence(self, test_uuids):
        server_state = get_state()
        user = User("test_user")
        server_state.users[user.username] = user
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        config = {"notify_presence": True, "broadcast_presence_with_user_lists": True}
        channel = Channel("test", channel_config=config)
        channel.add_connection(connection)
        channel.remove_connection(connection)

    def test_add_connection_w_presence(self, test_uuids):
        server_state = get_state()
        user = User("test_user")
        server_state.users[user.username] = user
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        config = {"notify_presence": True, "broadcast_presence_with_user_lists": True}
        channel = Channel("test", channel_config=config)
        channel.add_connection(connection)
        assert len(channel.connections["test_user"]) == 1
        assert "test_user" in channel.connections
        assert connection in channel.connections["test_user"]

    def test_presence_message(self, test_uuids):
        user = User("test_user")
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        channel = Channel("test")
        channel.add_connection(connection)
        payload = channel.send_notify_presence_info("test_user", "join")
        assert payload["user"] == "test_user"
        assert payload["message"]["action"] == "join"
        assert payload["type"] == "presence"
        assert payload["channel"] == "test"
        assert len(payload["users"]) == 0

    def test_presence_message_w_users(self, test_uuids):
        server_state = get_state()
        user = User("test_user")
        user.state_from_dict({"key": "1", "key2": "2"})
        user.state_public_keys = ["key2"]
        server_state.users[user.username] = user
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        user2 = User("test_user2")
        user2.state_from_dict({"key": "1", "key2": "2"})
        server_state.users[user2.username] = user2
        connection2 = Connection("test_user2", conn_id=test_uuids[2])
        user2.add_connection(connection2)
        config = {"notify_presence": True, "broadcast_presence_with_user_lists": True}
        channel = Channel("test", channel_config=config)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        payload = channel.send_notify_presence_info("test_user", "join")
        assert len(payload["users"]) == 2
        sorted_users = sorted(payload["users"], key=lambda x: x["user"])
        assert sorted_users == [
            {"state": {"key2": "2"}, "user": "test_user"},
            {"state": {}, "user": "test_user2"},
        ]

    def test_history(self):
        config = {"store_history": True, "history_size": 3}
        channel = Channel("test", long_name="long name", channel_config=config)
        channel.add_message(
            {
                "channel": "test",
                "message": "test1",
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            }
        )
        channel.add_message(
            {
                "channel": "test",
                "message": "test2",
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            }
        )
        channel.add_message(
            {
                "channel": "test",
                "message": "test3",
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            }
        )
        channel.add_message(
            {
                "channel": "test",
                "message": "test4",
                "type": "message",
                "no_history": True,
                "pm_users": [],
                "exclude_users": [],
            }
        )
        channel.add_message(
            {
                "channel": "test",
                "message": "test5",
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            }
        )

        assert len(channel.history) == 3
        assert channel.history == [
            {
                "channel": "test",
                "message": "test2",
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            },
            {
                "channel": "test",
                "message": "test3",
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            },
            {
                "channel": "test",
                "message": "test5",
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            },
        ]

    def test_user_state(self, test_uuids):
        user = User("test_user")
        changed = user.state_from_dict({"key": "1", "key2": "2"})
        user.state_public_keys = ["key2"]
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        channel = Channel("test")
        channel.add_connection(connection)
        payload = channel.send_user_state(user, changed)
        assert payload["user"] == "test_user"
        assert payload["message"]["state"] == {"key2": "2"}
        assert payload["message"]["changed"] == [{"key": "key2", "value": "2"}]
        assert payload["type"] == "user_state_change"
        assert payload["channel"] == "test"

    def test_user_single_assignment(self, test_uuids):
        server_state = get_state()
        user = User("test_user")
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        channel = Channel("test")
        server_state.channels[channel.name] = channel
        channel.add_connection(connection)
        assert [channel] == user.get_channels()

    def test_user_multi_assignment(self, test_uuids):
        server_state = get_state()
        user = User("test_user")
        connection = Connection("test_user", conn_id=test_uuids[1])
        connection2 = Connection("test_user", conn_id=test_uuids[2])
        connection3 = Connection("test_user", conn_id=test_uuids[3])
        user.add_connection(connection)
        user.add_connection(connection2)
        user.add_connection(connection3)
        channel = Channel("test")
        channel2 = Channel("test2")
        server_state.channels[channel.name] = channel
        server_state.channels[channel2.name] = channel2
        channel.add_connection(connection)
        channel.add_connection(connection2)
        channel2.add_connection(connection3)
        assert ["test", "test2"] == sorted([c.name for c in user.get_channels()])


@pytest.mark.usefixtures("cleanup_globals")
class TestConnection(object):
    def test_create_defaults(self, test_uuids):
        now = datetime.utcnow()
        connection = Connection("test", test_uuids[1])
        assert connection.username == "test"
        assert now <= connection.last_active
        assert connection.socket is None
        assert connection.queue is None
        assert connection.id == test_uuids[1]

    def test_mark_for_gc(self, test_uuids):
        long_time_ago = datetime.utcnow() - timedelta(days=50)
        connection = Connection("test", test_uuids[1])
        connection.mark_for_gc()
        assert connection.last_active < long_time_ago

    def test_message(self, test_uuids):
        connection = Connection("test", test_uuids[1])
        connection.queue = Queue()
        connection.add_message({"message": "test"})
        assert connection.queue.get() == [{"message": "test"}]

    def test_heartbeat(self, test_uuids):
        connection = Connection("test", test_uuids[1])
        connection.queue = Queue()
        connection.heartbeat()
        assert connection.queue.get() == []


class TestUser(object):
    def test_create_defaults(self):
        user = User("test_user")
        user.state_from_dict({"key": "1", "key2": "2"})
        user.state_public_keys = ["key2"]
        assert repr(user) == "<User:test_user, connections:0>"
        assert sorted(user.state.items()) == sorted({"key": "1", "key2": "2"}.items())
        assert user.public_state == {"key2": "2"}

    def test_messages(self, test_uuids):
        user = User("test_user")
        connection = Connection("test_user", conn_id=test_uuids[1])
        connection.queue = Queue()
        connection2 = Connection("test_user", conn_id=test_uuids[2])
        connection2.queue = Queue()
        user.add_connection(connection)
        user.add_connection(connection2)
        user.add_message(
            {
                "type": "message",
                "no_history": False,
                "pm_users": [],
                "exclude_users": [],
            }
        )
        assert len(user.connections) == 2
        assert len(user.connections[0].queue.get()) == 1
        assert len(user.connections[1].queue.get()) == 1


@pytest.mark.usefixtures("cleanup_globals")
class TestGC(object):
    def test_gc_connections_active(self, test_uuids):
        server_state = get_state()
        channel = Channel("test")
        server_state.channels[channel.name] = channel
        channel2 = Channel("test2")
        server_state.channels[channel2.name] = channel2
        user = User("test_user")
        server_state.users[user.username] = user
        user2 = User("test_user2")
        server_state.users[user2.username] = user2
        connection = Connection("test_user", test_uuids[1])
        server_state.connections[connection.id] = connection
        connection2 = Connection("test_user", test_uuids[2])
        server_state.connections[connection2.id] = connection2
        connection3 = Connection("test_user2", test_uuids[3])
        server_state.connections[connection3.id] = connection3
        connection4 = Connection("test_user2", test_uuids[4])
        server_state.connections[connection4.id] = connection4
        user.add_connection(connection)
        user.add_connection(connection2)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        user2.add_connection(connection3)
        user2.add_connection(connection4)
        channel2.add_connection(connection3)
        channel2.add_connection(connection4)
        channelstream.gc.gc_conns()
        conns = server_state.channels["test"].connections["test_user"]
        assert len(conns) == 2
        assert len(server_state.connections.items()) == 4
        conns = server_state.channels["test2"].connections["test_user2"]
        assert len(conns) == 2
        assert len(user.connections) == 2
        assert len(user2.connections) == 2
        assert sorted(channel.connections.keys()) == ["test_user"]
        assert sorted(channel2.connections.keys()) == ["test_user2"]

    def test_gc_connections_collecting(self, test_uuids):
        server_state = get_state()
        channel = Channel("test")
        server_state.channels[channel.name] = channel
        channel2 = Channel("test2")
        server_state.channels[channel2.name] = channel2
        user = User("test_user")
        server_state.users[user.username] = user
        user2 = User("test_user2")
        server_state.users[user2.username] = user2
        connection = Connection("test_user", test_uuids[1])
        server_state.connections[connection.id] = connection
        connection2 = Connection("test_user", test_uuids[2])
        connection2.mark_for_gc()
        server_state.connections[connection2.id] = connection2
        connection3 = Connection("test_user2", test_uuids[3])
        connection3.mark_for_gc()
        server_state.connections[connection3.id] = connection3
        connection4 = Connection("test_user2", test_uuids[4])
        server_state.connections[connection4.id] = connection4
        user.add_connection(connection)
        user.add_connection(connection2)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        user2.add_connection(connection3)
        user2.add_connection(connection4)
        channel2.add_connection(connection3)
        channel2.add_connection(connection4)
        channelstream.gc.gc_conns()
        assert len(server_state.connections.items()) == 2
        conns = server_state.channels["test"].connections["test_user"]
        assert len(conns) == 1
        assert conns == [connection]
        conns = server_state.channels["test2"].connections["test_user2"]
        assert len(conns) == 1
        assert conns == [connection4]
        assert len(user.connections) == 1
        assert len(user2.connections) == 1
        connection.mark_for_gc()
        connection4.mark_for_gc()
        channelstream.gc.gc_conns()
        assert "test_user" not in server_state.channels["test"].connections
        assert "test_user2" not in server_state.channels["test2"].connections
        assert len(server_state.channels["test"].connections.items()) == 0
        assert len(server_state.channels["test2"].connections.items()) == 0

    def test_users_active(self):
        server_state = get_state()
        user = User("test_user")
        server_state.users[user.username] = user
        user2 = User("test_user2")
        server_state.users[user2.username] = user2
        channelstream.gc.gc_users()
        assert len(server_state.users.items()) == 2
        user.last_active -= timedelta(days=2)
        channelstream.gc.gc_users()
        assert len(server_state.users.items()) == 1
