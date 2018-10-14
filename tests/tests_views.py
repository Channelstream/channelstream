from gevent import monkey

monkey.patch_all()

import pytest
import gevent
import marshmallow
from channelstream.server_state import get_state
from channelstream.channel import Channel


@pytest.mark.usefixtures("cleanup_globals", "pyramid_config")
class TestConnectViews(object):
    def test_bad_json(self, dummy_request, test_uuids):
        from channelstream.wsgi_views.server import connect

        dummy_request.json_body = {}
        try:
            connect(dummy_request)
        except marshmallow.exceptions.ValidationError as exc:
            assert exc.messages == {"username": ["Missing data for required field."]}

    def test_good_json(self, dummy_request, test_uuids):
        server_state = get_state()
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
        assert server_state.channels == {}
        result = connect(dummy_request)
        assert len(server_state.channels.keys()) == 2
        assert "username" in server_state.users
        assert test_uuids[1] in server_state.connections
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
    def test_bad_json(self, dummy_request, test_uuids):
        from channelstream.wsgi_views.server import user_state

        dummy_request.json_body = {}
        with pytest.raises(marshmallow.exceptions.ValidationError) as excinfo:
            user_state(dummy_request)
        assert excinfo.value.messages == {"user": ["Missing data for required field."]}

    def _connect_user(self, dummy_request, test_uuids):
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

    def test_not_found_json(self, dummy_request, test_uuids):
        from channelstream.wsgi_views.server import user_state

        dummy_request.json_body = {"user": "blabla"}
        with pytest.raises(marshmallow.exceptions.ValidationError) as excinfo:
            user_state(dummy_request)
        assert excinfo.value.messages == {"user": ["Unknown user"]}

    def test_good_json(self, dummy_request, test_uuids):
        from channelstream.wsgi_views.server import user_state

        self._connect_user(dummy_request, test_uuids)
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

    def test_good_json_no_public_keys(self, dummy_request, test_uuids):
        from channelstream.wsgi_views.server import user_state

        self._connect_user(dummy_request, test_uuids)
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

    def test_good_json(self, dummy_request, test_uuids):
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
    def test_bad_json(self, dummy_request, test_uuids):
        from channelstream.wsgi_views.server import unsubscribe

        dummy_request.json_body = {}
        try:
            unsubscribe(dummy_request)
        except marshmallow.exceptions.ValidationError as exc:
            assert list(sorted(exc.messages.keys())) == ["channels", "conn_id"]

    def test_good_json(self, dummy_request, test_uuids):
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

    def test_non_existing_channel(self, dummy_request, test_uuids):
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

    def test_no_channels(self, dummy_request, test_uuids):
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

    def test_subscribed_json(self, dummy_request, test_uuids):
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
        comp_a = sorted(result["channels"]["a"]["users"])
        comp_b = sorted(["test1", "test2"])
        assert comp_a == comp_b
        assert result["channels"]["a"]["total_users"] == 2
        assert result["channels"]["a"]["total_connections"] == 2
        assert result["channels"]["c"]["users"] == ["test2"]
        assert result["channels"]["c"]["total_users"] == 1
        assert result["channels"]["c"]["total_connections"] == 1
        assert result["channels"]["aB"]["users"] == ["test1"]
        comp_a = sorted(result["users"], key=lambda x: x["user"])
        comp_b = sorted(
            [
                {"state": {"bar": "baz", "key": "foo"}, "user": "test1"},
                {"state": {"bar": "baz1", "key": "foo1"}, "user": "test2"},
            ],
            key=lambda x: x["user"],
        )
        assert comp_a == comp_b
        dummy_request.body = "NOTEMPTY"
        dummy_request.json_body = {"info": {"channels": ["a"]}}
        result = info(dummy_request)
        assert "a" in result["channels"]
        assert "aB" not in result["channels"]

    def test_detailed_json(self, dummy_request, test_uuids):
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

        server_state = get_state()
        dummy_request.json_body = {}
        assert server_state.stats["total_unique_messages"] == 0

        with pytest.raises(marshmallow.exceptions.ValidationError) as excinfo:
            message(dummy_request)
        assert excinfo.value.messages == {"_schema": ["Invalid input type."]}

    def test_good_json_no_channel(self, dummy_request):
        from channelstream.wsgi_views.server import message

        server_state = get_state()
        channel = Channel("test")
        channel.store_history = True
        server_state.channels[channel.name] = channel
        msg_payload = {
            "type": "message",
            "user": "system",
            "channel": "test",
            "message": {"text": "test"},
        }

        dummy_request.json_body = [msg_payload]
        assert server_state.stats["total_unique_messages"] == 0
        assert len(channel.history) == 0
        message(dummy_request)
        # change context
        gevent.sleep(0)
        assert server_state.stats["total_unique_messages"] == 1
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

        server_state = get_state()
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
        connection = server_state.users["test1"].connections[0]
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
        with pytest.raises(marshmallow.exceptions.ValidationError) as excinfo:
            message(dummy_request)
        assert excinfo.value.messages == {"_schema": ["Invalid input type."]}

    def test_good_json_no_channel(self, dummy_request):
        from channelstream.wsgi_views.server import message, messages_patch

        server_state = get_state()
        channel = Channel("test")
        channel.store_history = True
        server_state.channels[channel.name] = channel
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

        server_state = get_state()
        channel = Channel("test")
        channel.store_history = True
        server_state.channels[channel.name] = channel
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
