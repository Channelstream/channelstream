from gevent import monkey

monkey.patch_all()

import pprint
import uuid
import pytest
import mock
import gevent
from datetime import datetime, timedelta
from gevent.queue import Queue
import marshmallow
from pyramid import testing
from channelstream import server_state
import channelstream.gc
from channelstream.channel import Channel
from channelstream.connection import Connection
from channelstream.user import User

test_uuids = [
    uuid.UUID("12345678-1234-5678-1234-567812345678"),
    uuid.UUID("22345678-1234-5678-1234-567812345678"),
    uuid.UUID("32345678-1234-5678-1234-567812345678"),
    uuid.UUID("42345678-1234-5678-1234-567812345678"),
    uuid.UUID("52345678-1234-5678-1234-567812345678"),
    uuid.UUID("62345678-1234-5678-1234-567812345678"),
    uuid.UUID("72345678-1234-5678-1234-567812345678"),
    uuid.UUID("82345678-1234-5678-1234-567812345678"),
    uuid.UUID("92345678-1234-5678-1234-567812345678"),
]


@pytest.fixture
def cleanup_globals():
    server_state.CHANNELS = {}
    server_state.CONNECTIONS = {}
    server_state.USERS = {}
    server_state.STATS = {
        "total_messages": 0,
        "total_unique_messages": 0,
        "started_on": datetime.utcnow(),
    }


@pytest.mark.usefixtures("cleanup_globals")
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

    def test_add_connection(self):
        connection = Connection("test_user", conn_id=test_uuids[1])
        channel = Channel("test")
        channel.add_connection(connection)
        assert len(channel.connections["test_user"]) == 1
        assert "test_user" in channel.connections
        assert connection in channel.connections["test_user"]
        assert repr(channel) == "<Channel: test, connections:1>"

    def test_remove_connection(self):
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

    def test_remove_non_existant_connection(self):
        channel = Channel("test")
        connection = Connection("test_user", conn_id=test_uuids[1])
        channel.remove_connection(connection)
        assert "test_user" not in channel.connections

    def test_remove_connection_w_presence(self):
        user = User("test_user")
        server_state.USERS[user.username] = user
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        config = {"notify_presence": True, "broadcast_presence_with_user_lists": True}
        channel = Channel("test", channel_config=config)
        channel.add_connection(connection)
        channel.remove_connection(connection)

    def test_add_connection_w_presence(self):
        user = User("test_user")
        server_state.USERS[user.username] = user
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        config = {"notify_presence": True, "broadcast_presence_with_user_lists": True}
        channel = Channel("test", channel_config=config)
        channel.add_connection(connection)
        assert len(channel.connections["test_user"]) == 1
        assert "test_user" in channel.connections
        assert connection in channel.connections["test_user"]

    def test_presence_message(self):
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

    def test_presence_message_w_users(self):
        user = User("test_user")
        user.state_from_dict({"key": "1", "key2": "2"})
        user.state_public_keys = ["key2"]
        server_state.USERS[user.username] = user
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        user2 = User("test_user2")
        user2.state_from_dict({"key": "1", "key2": "2"})
        server_state.USERS[user2.username] = user2
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

    def test_user_state(self):
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

    def test_user_single_assignment(self):
        user = User("test_user")
        connection = Connection("test_user", conn_id=test_uuids[1])
        user.add_connection(connection)
        channel = Channel("test")
        server_state.CHANNELS[channel.name] = channel
        channel.add_connection(connection)
        assert [channel] == user.get_channels()

    def test_user_multi_assignment(self):
        user = User("test_user")
        connection = Connection("test_user", conn_id=test_uuids[1])
        connection2 = Connection("test_user", conn_id=test_uuids[2])
        connection3 = Connection("test_user", conn_id=test_uuids[3])
        user.add_connection(connection)
        user.add_connection(connection2)
        user.add_connection(connection3)
        channel = Channel("test")
        channel2 = Channel("test2")
        server_state.CHANNELS[channel.name] = channel
        server_state.CHANNELS[channel2.name] = channel2
        channel.add_connection(connection)
        channel.add_connection(connection2)
        channel2.add_connection(connection3)
        assert ["test", "test2"] == sorted([c.name for c in user.get_channels()])


@pytest.mark.usefixtures("cleanup_globals")
class TestConnection(object):
    def test_create_defaults(self):
        now = datetime.utcnow()
        connection = Connection("test", test_uuids[1])
        assert connection.username == "test"
        assert now <= connection.last_active
        assert connection.socket is None
        assert connection.queue is None
        assert connection.id == test_uuids[1]

    def test_mark_for_gc(self):
        long_time_ago = datetime.utcnow() - timedelta(days=50)
        connection = Connection("test", test_uuids[1])
        connection.mark_for_gc()
        assert connection.last_active < long_time_ago

    def test_message(self):
        connection = Connection("test", test_uuids[1])
        connection.queue = Queue()
        connection.add_message({"message": "test"})
        assert connection.queue.get() == [{"message": "test"}]

    def test_heartbeat(self):
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

    def test_messages(self):
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
    def test_gc_connections_active(self):
        channel = Channel("test")
        server_state.CHANNELS[channel.name] = channel
        channel2 = Channel("test2")
        server_state.CHANNELS[channel2.name] = channel2
        user = User("test_user")
        server_state.USERS[user.username] = user
        user2 = User("test_user2")
        server_state.USERS[user2.username] = user2
        connection = Connection("test_user", test_uuids[1])
        server_state.CONNECTIONS[connection.id] = connection
        connection2 = Connection("test_user", test_uuids[2])
        server_state.CONNECTIONS[connection2.id] = connection2
        connection3 = Connection("test_user2", test_uuids[3])
        server_state.CONNECTIONS[connection3.id] = connection3
        connection4 = Connection("test_user2", test_uuids[4])
        server_state.CONNECTIONS[connection4.id] = connection4
        user.add_connection(connection)
        user.add_connection(connection2)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        user2.add_connection(connection3)
        user2.add_connection(connection4)
        channel2.add_connection(connection3)
        channel2.add_connection(connection4)
        channelstream.gc.gc_conns()
        conns = server_state.CHANNELS["test"].connections["test_user"]
        assert len(conns) == 2
        assert len(server_state.CONNECTIONS.items()) == 4
        conns = server_state.CHANNELS["test2"].connections["test_user2"]
        assert len(conns) == 2
        assert len(user.connections) == 2
        assert len(user2.connections) == 2
        assert sorted(channel.connections.keys()) == ["test_user"]
        assert sorted(channel2.connections.keys()) == ["test_user2"]

    def test_gc_connections_collecting(self):
        channel = Channel("test")
        server_state.CHANNELS[channel.name] = channel
        channel2 = Channel("test2")
        server_state.CHANNELS[channel2.name] = channel2
        user = User("test_user")
        server_state.USERS[user.username] = user
        user2 = User("test_user2")
        server_state.USERS[user2.username] = user2
        connection = Connection("test_user", test_uuids[1])
        server_state.CONNECTIONS[connection.id] = connection
        connection2 = Connection("test_user", test_uuids[2])
        connection2.mark_for_gc()
        server_state.CONNECTIONS[connection2.id] = connection2
        connection3 = Connection("test_user2", test_uuids[3])
        connection3.mark_for_gc()
        server_state.CONNECTIONS[connection3.id] = connection3
        connection4 = Connection("test_user2", test_uuids[4])
        server_state.CONNECTIONS[connection4.id] = connection4
        user.add_connection(connection)
        user.add_connection(connection2)
        channel.add_connection(connection)
        channel.add_connection(connection2)
        user2.add_connection(connection3)
        user2.add_connection(connection4)
        channel2.add_connection(connection3)
        channel2.add_connection(connection4)
        channelstream.gc.gc_conns()
        assert len(server_state.CONNECTIONS.items()) == 2
        conns = server_state.CHANNELS["test"].connections["test_user"]
        assert len(conns) == 1
        assert conns == [connection]
        conns = server_state.CHANNELS["test2"].connections["test_user2"]
        assert len(conns) == 1
        assert conns == [connection4]
        assert len(user.connections) == 1
        assert len(user2.connections) == 1
        connection.mark_for_gc()
        connection4.mark_for_gc()
        channelstream.gc.gc_conns()
        assert "test_user" not in server_state.CHANNELS["test"].connections
        assert "test_user2" not in server_state.CHANNELS["test2"].connections
        assert len(server_state.CHANNELS["test"].connections.items()) == 0
        assert len(server_state.CHANNELS["test2"].connections.items()) == 0

    def test_users_active(self):
        user = User("test_user")
        server_state.USERS[user.username] = user
        user2 = User("test_user2")
        server_state.USERS[user2.username] = user2
        channelstream.gc.gc_users()
        assert len(server_state.USERS.items()) == 2
        user.last_active -= timedelta(days=2)
        channelstream.gc.gc_users()
        assert len(server_state.USERS.items()) == 1


@pytest.fixture
def pyramid_config():
    # from pyramid.request import Request
    # request = Request.blank('/', base_url='http://foo.com')
    config = testing.setUp(settings={})
    settings = config.get_settings()
    return config, settings


@pytest.fixture
def dummy_request():
    app_request = testing.DummyRequest()
    app_request.handle_cors = mock.Mock()
    return app_request


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestConnectViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import connect

        dummy_request.json_body = {}
        try:
            connect(dummy_request)
        except marshmallow.exceptions.ValidationError as exc:
            assert exc.messages == {"username": ["Missing data for required field."]}

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import connect

        dummy_request.json_body = {
            "username": "username",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz"},
            "state_public_keys": ["bar"],
            "channels": ["a", "aB"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }
        assert server_state.CHANNELS == {}
        result = connect(dummy_request)
        assert len(server_state.CHANNELS.keys()) == 2
        assert "username" in server_state.USERS
        assert test_uuids[1] in server_state.CONNECTIONS
        assert result["channels"] == ["a", "aB"]
        assert result["state"] == {"bar": "baz", "key": "foo"}
        assert result["conn_id"] == test_uuids[1]
        channels_info = result["channels_info"]["channels"]
        assert len(channels_info.keys()) == 2
        assert channels_info["a"]["total_users"] == 1
        assert channels_info["a"]["total_connections"] == 1
        assert channels_info["a"]["users"] == ["username"]
        assert channels_info["a"]["history"] == []
        assert result["channels_info"]["users"] == [
            {"state": {"bar": "baz", "key": "foo"}, "user": "username"}
        ]


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestUserStateViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import user_state

        dummy_request.json_body = {}
        with pytest.raises(marshmallow.exceptions.ValidationError) as excinfo:
            user_state(dummy_request)
        assert excinfo.value.messages == {"user": ["Missing data for required field."]}

    def _connect_user(self):
        from channelstream.wsgi_views.server import connect

        dummy_request.json_body = {
            "username": "test",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz"},
            "state_public_keys": ["bar"],
            "channels": ["a", "aB"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)

    def test_not_found_json(self, dummy_request):
        from channelstream.wsgi_views.server import user_state

        dummy_request.json_body = {"user": "blabla"}
        with pytest.raises(marshmallow.exceptions.ValidationError) as excinfo:
            user_state(dummy_request)
        assert excinfo.value.messages == {"user": ["Unknown user"]}

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import user_state

        self._connect_user()
        dummy_request.json_body = {
            "user": "test",
            "user_state": {"bar": 2, "private": "im_private"},
            "state_public_keys": ["avatar", "bar"],
        }
        result = user_state(dummy_request)
        sorted_keys = sorted(["bar", "key", "private"])
        assert sorted_keys == sorted(result["user_state"].keys())
        assert result["user_state"]["private"] == "im_private"
        sorted_changed = sorted([x["key"] for x in result["changed_state"]])
        assert result["public_keys"] == ["avatar", "bar"]
        assert sorted_changed == sorted(["bar", "private"])

    def test_good_json_no_public_keys(self, dummy_request):
        from channelstream.wsgi_views.server import user_state

        self._connect_user()
        dummy_request.json_body = {
            "user": "test",
            "user_state": {"bar": 2, "private": "im_private"},
        }
        result = user_state(dummy_request)
        sorted_keys = sorted(["bar", "key", "private"])
        assert sorted_keys == sorted(result["user_state"].keys())
        assert result["user_state"]["private"] == "im_private"
        assert result["public_keys"] == ["bar"]
        sorted_changed = sorted([x["key"] for x in result["changed_state"]])
        assert sorted_changed == sorted(["bar", "private"])


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestSubscribeViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import subscribe

        dummy_request.json_body = {}
        try:
            subscribe(dummy_request)
        except marshmallow.exceptions.ValidationError as exc:
            assert list(sorted(exc.messages.keys())) == ["channels", "conn_id"]

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import connect, subscribe

        dummy_request.json_body = {
            "username": "test",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz"},
            "state_public_keys": ["bar"],
            "channels": ["a", "aB"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)
        dummy_request.json_body = {
            "conn_id": str(test_uuids[1]),
            "channels": ["b"],
            "channel_configs": {
                "a": {"notify_presence": True},
                "b": {"notify_presence": True},
            },
        }
        result = subscribe(dummy_request)
        assert sorted(result["channels"]) == sorted(["a", "aB", "b"])
        assert result["channels_info"]["users"] == [
            {"state": {"bar": "baz", "key": "foo"}, "user": "test"}
        ]
        assert "a" in result["channels_info"]["channels"]
        assert "b" in result["channels_info"]["channels"]
        assert result["channels_info"]["channels"]["a"]["total_connections"] == 1
        assert result["channels_info"]["channels"]["a"]["total_users"] == 1
        assert result["channels_info"]["channels"]["a"]["history"] == []
        assert result["channels_info"]["channels"]["a"]["users"] == ["test"]


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestUnsubscribeViews(object):
    def test_bad_json(self, dummy_request):
        from channelstream.wsgi_views.server import unsubscribe

        dummy_request.json_body = {}
        try:
            unsubscribe(dummy_request)
        except marshmallow.exceptions.ValidationError as exc:
            assert list(sorted(exc.messages.keys())) == ["channels", "conn_id"]

    def test_good_json(self, dummy_request):
        from channelstream.wsgi_views.server import connect, unsubscribe

        dummy_request.json_body = {
            "username": "test",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz"},
            "state_public_keys": ["bar"],
            "channels": ["a", "aB", "aC"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)
        dummy_request.json_body = {
            "conn_id": str(test_uuids[1]),
            "channels": ["aC", "a"],
        }
        result = unsubscribe(dummy_request)
        assert sorted(result["channels"]) == sorted(["aB"])

    def test_non_existing_channel(self, dummy_request):
        from channelstream.wsgi_views.server import connect, unsubscribe

        dummy_request.json_body = {
            "username": "test",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz"},
            "state_public_keys": ["bar"],
            "channels": ["a", "aB", "aC"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }

        connect(dummy_request)
        dummy_request.json_body = {"conn_id": str(test_uuids[1]), "channels": ["d"]}
        result = unsubscribe(dummy_request)
        assert sorted(result["channels"]) == sorted(["a", "aB", "aC"])

    def test_no_channels(self, dummy_request):
        from channelstream.wsgi_views.server import connect, unsubscribe

        dummy_request.json_body = {
            "username": "test",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz"},
            "state_public_keys": ["bar"],
            "channels": ["a"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)
        dummy_request.json_body = {"conn_id": str(test_uuids[1]), "channels": ["a"]}
        result = unsubscribe(dummy_request)
        assert len(result["channels"]) == 0
        assert result["channels_info"]["users"] == []
        assert result["channels_info"]["channels"] == {}


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestInfoView(object):
    def test_empty_json(self, dummy_request):
        from channelstream.wsgi_views.server import info

        dummy_request.json_body = {}
        result = info(dummy_request)
        assert result["channels"] == {}
        assert result["users"] == []

    def test_subscribed_json(self, dummy_request):
        from channelstream.wsgi_views.server import connect, info

        dummy_request.json_body = {
            "username": "test1",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz"},
            "state_public_keys": ["bar"],
            "channels": ["a", "aB"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)
        dummy_request.json_body = {
            "username": "test2",
            "conn_id": test_uuids[2],
            "fresh_user_state": {"key": "foo1"},
            "user_state": {"bar": "baz1"},
            "state_public_keys": ["key"],
            "channels": ["a", "c"],
            "channel_configs": {"c": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)
        dummy_request.json_body = {}
        result = info(dummy_request)
        assert sorted(("a", "aB", "c")) == sorted(result["channels"].keys())
        assert result["users"]
        compA = sorted(result["channels"]["a"]["users"])
        compB = sorted(["test1", "test2"])
        assert compA == compB
        assert result["channels"]["a"]["total_users"] == 2
        assert result["channels"]["a"]["total_connections"] == 2
        assert result["channels"]["c"]["users"] == ["test2"]
        assert result["channels"]["c"]["total_users"] == 1
        assert result["channels"]["c"]["total_connections"] == 1
        assert result["channels"]["aB"]["users"] == ["test1"]
        compA = sorted(result["users"], key=lambda x: x["user"])
        compB = sorted(
            [
                {"state": {"bar": "baz", "key": "foo"}, "user": "test1"},
                {"state": {"bar": "baz1", "key": "foo1"}, "user": "test2"},
            ],
            key=lambda x: x["user"],
        )
        assert compA == compB
        dummy_request.body = "NOTEMPTY"
        dummy_request.json_body = {"info": {"channels": ["a"]}}
        result = info(dummy_request)
        assert "a" in result["channels"]
        assert "aB" not in result["channels"]

    def test_detailed_json(self, dummy_request):
        from channelstream.wsgi_views.server import connect, info, message

        dummy_request.json_body = {
            "username": "test1",
            "conn_id": str(test_uuids[1]),
            "fresh_user_state": {"key": "foo"},
            "user_state": {"bar": "baz", "private": "p1"},
            "state_public_keys": ["bar"],
            "channels": ["a", "aB", "c", "D"],
            "channel_configs": {"a": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)
        dummy_request.json_body = [
            {
                "type": "message",
                "user": "test1",
                "channel": "a",
                "message": {"text": "test"},
            }
        ]
        message(dummy_request)
        gevent.sleep(0)
        dummy_request.body = "value"
        dummy_request.json_body = {
            "info": {
                "exclude_channels": ["c"],
                "include_history": False,
                "include_users": True,
                "return_public_state": True,
                "include_connections": True,
            }
        }
        result = info(dummy_request)
        assert sorted(result["channels"].keys()) == sorted(["a", "aB", "D"])
        assert "private" not in result["users"][0]["state"]
        assert len(result["channels"]["a"]["history"]) == 0


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestMessageViews(object):
    def test_empty_json(self, dummy_request):
        from channelstream.wsgi_views.server import message

        dummy_request.json_body = {}
        assert server_state.STATS["total_unique_messages"] == 0
        result = message(dummy_request)
        assert server_state.STATS["total_unique_messages"] == 0

    def test_good_json_no_channel(self, dummy_request):
        from channelstream.wsgi_views.server import message

        channel = Channel("test")
        channel.store_history = True
        server_state.CHANNELS[channel.name] = channel
        msg_payload = {
            "type": "message",
            "user": "system",
            "channel": "test",
            "message": {"text": "test"},
        }

        dummy_request.json_body = [msg_payload]
        assert server_state.STATS["total_unique_messages"] == 0
        assert len(channel.history) == 0
        message(dummy_request)
        # change context
        gevent.sleep(0)
        assert server_state.STATS["total_unique_messages"] == 1
        assert len(channel.history) == 1
        msg = channel.history[0]
        assert msg["uuid"] is not None
        assert msg["user"] == msg_payload["user"]
        assert msg["message"] == msg_payload["message"]
        assert msg["type"] == msg_payload["type"]
        assert msg["channel"] == msg_payload["channel"]
        assert msg["timestamp"] is not None

    def test_catchup_messages(self, dummy_request):
        from channelstream.wsgi_views.server import message, connect

        dummy_request.json_body = {
            "username": "test1",
            "channels": ["test"],
            "channel_configs": {"test": {"store_history": True, "history_size": 2}},
        }
        connect(dummy_request)
        msg_payload = {
            "type": "message",
            "user": "system",
            "channel": "test",
            "message": {"text": "test3"},
        }
        dummy_request.json_body = [msg_payload]
        message(dummy_request)
        # add pm message to non-existing user
        wrong_user_msg_payload = {
            "type": "message",
            "user": "system",
            "channel": "test",
            "message": {"text": "test1"},
            "pm_users": ["test2"],
        }
        msg_payload = {
            "type": "message",
            "user": "system",
            "channel": "test",
            "message": {"text": "test2"},
            "pm_users": ["test1"],
        }
        dummy_request.json_body = [wrong_user_msg_payload, msg_payload]
        message(dummy_request)
        # change context
        gevent.sleep(0)
        connection = server_state.USERS["test1"].connections[0]
        messages = connection.get_catchup_messages()
        assert len(messages) == 2
        assert messages[0]["timestamp"] > connection.last_active
        assert messages[0]["message"]["text"] == "test3"
        assert messages[1]["timestamp"] > connection.last_active
        assert messages[1]["message"]["text"] == "test2"


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestMessageEditViews(object):
    def test_empty_json(self, dummy_request):
        from channelstream.wsgi_views.server import message

        dummy_request.json_body = {}
        result = message(dummy_request)
        assert result == []

    def test_good_json_no_channel(self, dummy_request):
        from channelstream.wsgi_views.server import message, messages_patch

        channel = Channel("test")
        channel.store_history = True
        server_state.CHANNELS[channel.name] = channel
        msg_payload = {"user": "system", "channel": "test", "message": {"text": "test"}}
        dummy_request.json_body = [msg_payload]
        message(dummy_request)
        # change context
        gevent.sleep(0)
        msg = channel.history[0]
        assert msg["message"] == msg_payload["message"]
        edit_payload = {
            "uuid": msg["uuid"],
            "user": "edited_system",
            "channel": "test",
            "timestamp": "2010-01-01T01:01",
            "edited": "2010-01-01T01:02",
            "message": {"text": "edited_message"},
        }
        dummy_request.json_body = [edit_payload]
        response = messages_patch(dummy_request)[0]
        gevent.sleep(0)
        assert msg["user"] == response["user"]
        assert msg["message"] == response["message"]
        assert msg["edited"] == response["edited"]
        assert msg["timestamp"] == response["timestamp"]
        frame = channel.frames[0][1]
        assert id(frame) == id(msg)
        assert frame["user"] == response["user"]
        assert frame["message"] == response["message"]
        assert frame["edited"] == response["edited"]
        assert frame["timestamp"] == response["timestamp"]


class TestMessageDeleteViews(object):
    def test_empty_json(self, dummy_request):
        from channelstream.wsgi_views.server import messages_delete

        dummy_request.json_body = []
        result = messages_delete(dummy_request)
        assert result == []

    def test_good_json_no_channel(self, dummy_request):
        from channelstream.wsgi_views.server import message, messages_delete

        channel = Channel("test")
        channel.store_history = True
        server_state.CHANNELS[channel.name] = channel
        msg_payload = {"user": "system", "channel": "test", "message": {"text": "test"}}
        dummy_request.json_body = [msg_payload]
        message(dummy_request)
        # change context
        gevent.sleep(0)
        msg = channel.history[0]
        assert msg["message"] == msg_payload["message"]
        dummy_request.json_body = [{"uuid": str(msg["uuid"]), "channel": "test"}]
        response = messages_delete(dummy_request)
        gevent.sleep(0)
        assert response[0]["uuid"] == msg["uuid"]
        assert len(channel.history) == 0
        assert len(channel.frames) == 1
        assert channel.frames[0][1]["type"] == "message:delete"


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestChannelConfigView(object):
    def test_empty_json(self, dummy_request):
        from channelstream.wsgi_views.server import channel_config

        dummy_request.json_body = {}
        result = channel_config(dummy_request)
        assert result["channels"] == {}
        assert result["users"] == []

    def test_valid_json(self, dummy_request):
        from channelstream.wsgi_views.server import channel_config

        dummy_request.json_body = {
            "chanx1": {
                "notify_presence": True,
                "store_history": True,
                "history_size": 3,
                "broadcast_presence_with_user_lists": True,
                "notify_state": True,
                "store_frames": False,
            }
        }
        result = channel_config(dummy_request)
        channel_settings = result["channels"]["chanx1"]["settings"]
        assert channel_settings["notify_presence"] is True
        assert channel_settings["store_history"] is True
        assert channel_settings["history_size"] == 3
        assert channel_settings["broadcast_presence_with_user_lists"] is True
        assert channel_settings["notify_state"] is True
        assert channel_settings["store_frames"] is False
