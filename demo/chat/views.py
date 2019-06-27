import json
import logging
import random

import gevent
import requests
from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.view import view_config, view_defaults
from requests.auth import HTTPBasicAuth
from utils import make_server_request, send_welcome_message, ssl_rewriter

log = logging.getLogger(__name__)


POSSIBLE_CHANNELS = set(["pub_chan", "second_chanel", "notify"])

CHANNEL_CONFIGS = {
    "pub_chan": {
        "notify_presence": True,
        "notify_state": True,
        "store_history": True,
        "history_size": 10,
        "broadcast_presence_with_user_lists": True,
    },
    "notify": {"store_history": True, "history_size": 50, "notify_presence": True},
}


@view_defaults(
    route_name="section_action", renderer="json", permission=NO_PERMISSION_REQUIRED
)
class DemoViews(object):
    def __init__(self, request):
        self.request = request
        self.request.response.headers.add("Cache-Control", "no-cache, no-store")

    @view_config(route_name="/", renderer="templates/demo.jinja2")
    def demo(self):
        """Render demo page"""
        random_name = "anon_%s" % random.randint(1, 999999)
        return {"username": random_name, "ssl_rewriter": ssl_rewriter}

    @view_config(match_param=["section=demo", "action=connect"], request_method="POST")
    def connect(self):
        """handle authorization of users trying to connect/reconnect"""
        channels = self.request.json_body.get("channels") or []
        random_name = "anon_%s" % random.randint(1, 999999)
        username = self.request.json_body.get("username", random_name)
        state = self.request.json_body.get("state", {})
        payload = {
            "username": username,
            # where user should be subscribed
            "channels": channels,
            # what default state should be set when user is created on channelstream end
            "fresh_user_state": {
                "email": None,
                "status": None,
                "private": "is private",
                "bar": 1,
                "bool": True,
            },
            # update state to this values if user object already exists
            "user_state": state,
            # what state keys should be visible to other users
            "state_public_keys": ["email", "status", "bar", "color"],
            # return only public state in response
            "info": {"return_public_state": True},
            # set chanel configurations if channels don't exist yet
            "channel_configs": CHANNEL_CONFIGS,
        }
        result = make_server_request(self.request, payload, "/connect")
        self.request.response.status = result.status_code
        server_response = result.json()
        # add a demo message when user connects after a while
        gevent.spawn_later(2, send_welcome_message, self.request, username)
        return server_response

    @view_config(
        match_param=["section=demo", "action=user_state"], request_method="POST"
    )
    def user_state(self):
        """"can be used to subscribe specific connection to other channels"""
        request_data = self.request.json_body
        payload = {
            "user": request_data["username"],
            "user_state": {
                "color": request_data["update_state"]["user_state"]["color"],
                "private": "private {}".format(random.randint(1, 99999)),
            },
        }
        result = make_server_request(self.request, payload, "/user_state")
        self.request.response.status = result.status_code
        return result.json()

    @view_config(
        match_param=["section=demo", "action=subscribe"], request_method="POST"
    )
    def subscribe(self):
        """"can be used to subscribe specific connection to other channels"""
        request_data = self.request.json_body
        payload = {
            "conn_id": request_data.get("conn_id", ""),
            "channels": request_data.get("channels", []),
            "channel_configs": CHANNEL_CONFIGS,
        }
        result = make_server_request(self.request, payload, "/subscribe")
        self.request.response.status = result.status_code
        server_response = result.json()
        return server_response

    @view_config(
        match_param=["section=demo", "action=unsubscribe"], request_method="POST"
    )
    def unsubscribe(self):
        """"can be used to unsubscribe specific connection to other channels"""
        request_data = self.request.json_body
        payload = {
            "conn_id": request_data.get("conn_id", ""),
            "channels": request_data.get("channels", []),
        }
        result = make_server_request(self.request, payload, "/unsubscribe")
        self.request.response.status = result.status_code
        server_response = result.json()
        return server_response

    @view_config(match_param=["section=demo", "action=message"], request_method="POST")
    def message_post(self):
        """send message to channel/users"""
        request_data = self.request.json_body
        payload = {
            "type": "message",
            "user": request_data.get("user", "system"),
            "channel": request_data.get("channel", "unknown_channel"),
            "message": request_data.get("message"),
        }
        result = make_server_request(self.request, [payload], "/message")
        self.request.response.status = result.status_code
        return result.json()

    @view_config(
        match_param=["section=demo", "action=channel_config"], request_method="POST"
    )
    def channel_config(self):
        """configure channel defaults"""

        payload = [
            (
                "pub_chan",
                {"notify_presence": True, "store_history": True, "history_size": 20},
            ),
            (
                "second_channel",
                {
                    "notify_presence": False,
                    "salvageable": True,
                    "store_history": True,
                    "history_size": 100,
                },
            ),
        ]
        url = "http://127.0.0.1:%s/channel_config" % self.server_port
        response = requests.post(
            url, data=json.dumps(payload), headers=self.secret_headers
        ).json()
        return response

    @view_config(match_param=["section=demo", "action=info"])
    def info(self):
        """gets information for the "admin" demo page"""
        result = make_server_request(self.request, {}, "/admin/admin.json")
        self.request.response.status = result.status_code
        return result.json()

    @view_config(
        match_param=["section=demo", "action=message"], request_method="DELETE"
    )
    def message_delete(self):
        payload = {
            "uuid": self.request.json_body["uuid"],
            "channel": self.request.json_body["channel"],
        }
        result = make_server_request(
            self.request, [payload], "/message", method="delete"
        )
        self.request.response.status = result.status_code
        return result.json()

    @view_config(match_param=["section=demo", "action=message"], request_method="PATCH")
    def message_patch(self):
        payload = {
            "uuid": self.request.json_body["uuid"],
            "channel": self.request.json_body["channel"],
            "message": self.request.json_body["message"],
        }
        result = make_server_request(
            self.request, [payload], "/message", method="patch"
        )
        self.request.response.status = result.status_code
        return result.json()
