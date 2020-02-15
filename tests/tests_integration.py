from gevent import monkey

monkey.patch_all()

import copy
import pytest

from webtest import TestApp
from channelstream.cli import SHARED_DEFAULTS
from channelstream.cli.start import RoutingApplication


def gen_signature(secret):
    from itsdangerous import TimestampSigner

    signer = TimestampSigner(secret)
    return signer.sign("channelstream")


@pytest.mark.usefixtures("cleanup_globals")
class TestServerConfigView(object):
    def test_defaults(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        app.get("/", status=404)
        app.post("/connect", status=403)

    def test_enforce_https_wrong(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        config["enforce_https"] = True
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        app.get("/", status=406)
        app.post("/connect", status=406)

    def test_enforce_https_proper(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        config["enforce_https"] = True
        application = RoutingApplication(config)
        app = TestApp(
            application,
            extra_environ={"REMOTE_ADDR": "127.0.0.1", "wsgi.url_scheme": "https"},
        )
        app.get("/", status=404)
        app.post("/connect", status=403)

    def test_connect_empty(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        secret_headers = {
            "x-channelstream-secret": gen_signature(SHARED_DEFAULTS["secret"]),
            "Content-Type": "application/json",
        }
        app.post_json("/connect", params={}, headers=secret_headers, status=422)

    def test_connect_minimal(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        secret_headers = {
            "x-channelstream-secret": gen_signature(SHARED_DEFAULTS["secret"]),
            "Content-Type": "application/json",
        }
        payload = {
            "username": "user_123",
            # where user should be subscribed
            "channels": ["a"],
        }
        result = app.post_json("/connect", params=payload, headers=secret_headers)
        assert "conn_id" in result.json
        assert "state" in result.json
        assert "username" in result.json
        assert "public_state" in result.json
        assert result.json["channels"] == ["a"]
        assert "channels_info" in result.json
        assert "a" in result.json["channels"]
        channel_a = result.json["channels_info"]["channels"]["a"]
        assert "uuid" in channel_a
        assert "name" in channel_a
        assert "long_name" in channel_a
        assert "last_active" in channel_a
        assert channel_a["total_connections"] == 1
        assert channel_a["total_users"] == 1
        assert channel_a["users"] == ["user_123"]
        assert channel_a["total_connections"] == 1
        assert channel_a["settings"]["notify_presence"] is False
        assert channel_a["settings"]["store_history"] is False
        assert channel_a["settings"]["history_size"] == 10
        assert channel_a["settings"]["broadcast_presence_with_user_lists"] is False
        assert channel_a["settings"]["notify_presence"] is False
        assert channel_a["settings"]["notify_state"] is False
        assert channel_a["settings"]["store_frames"] is True
        assert channel_a["settings"]["store_frames"] is True
        assert len(channel_a["history"]) == 0
        assert len(result.json["channels_info"]["users"]) == 1
        assert result.json["channels_info"]["users"][0] == {
            "user": "user_123",
            "state": {},
        }

    def test_connect_good(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        secret_headers = {
            "x-channelstream-secret": gen_signature(SHARED_DEFAULTS["secret"]),
            "Content-Type": "application/json",
        }
        CHANNEL_CONFIGS = {
            "pub_chan": {
                "notify_presence": True,
                "notify_state": True,
                "store_history": True,
                "history_size": 10,
                "broadcast_presence_with_user_lists": True,
            },
            "notify": {
                "store_history": True,
                "history_size": 50,
                "notify_presence": True,
            },
        }

        payload = {
            "username": "user_123",
            # where user should be subscribed
            "channels": ["a", "b"],
            # what default state should be set when user is created on channelstream end
            "fresh_user_state": {
                "status": "active",
                "private": "is private",
                "bar": 1,
                "bool": True,
            },
            # update state to this values if user object already exists
            "user_state": {},
            # what state keys should be visible to other users
            "state_public_keys": ["status", "bar", "color"],
            # return only public state in response
            "info": {"return_public_state": True},
            # set chanel configurations if channels don't exist yet
            "channel_configs": CHANNEL_CONFIGS,
        }
        app.post_json("/connect", params=payload, headers=secret_headers)

    def test_message_minimal(self):
        config = copy.deepcopy(SHARED_DEFAULTS)
        application = RoutingApplication(config)
        app = TestApp(application, extra_environ={"REMOTE_ADDR": "127.0.0.1"})
        secret_headers = {
            "x-channelstream-secret": gen_signature(SHARED_DEFAULTS["secret"]),
            "Content-Type": "application/json",
        }
        payload = {
            "type": "message",
            "user": "system",
            "channel": "some_chan",
            "message": {"text": "my_text"},
        }
        result = app.post_json("/message", params=[payload], headers=secret_headers)
        message = result.json[0]
        assert len(message["pm_users"]) == 0
        assert len(message["exclude_users"]) == 0
        assert message["channel"] == "some_chan"
        assert message["no_history"] is False
        assert message["edited"] is None
        assert "uuid" in message
        assert "timestamp" in message
        assert message["user"] == "system"
        assert message["message"] == {"text": "my_text"}
