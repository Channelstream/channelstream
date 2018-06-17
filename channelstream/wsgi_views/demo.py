import json
import random
import uuid
import requests
import six
import gevent
import logging
from pyramid.view import view_config, view_defaults
from pyramid.security import NO_PERMISSION_REQUIRED
from itsdangerous import TimestampSigner
from requests.auth import HTTPBasicAuth

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


def make_server_request(request, payload, endpoint, auth=None):
    """
    makes a json request to channelstream server endpoint signing the request and sending the payload
    :param request:
    :param payload:
    :param endpoint:
    :param auth:
    :return:
    """
    server_port = request.registry.settings["port"]
    signer = TimestampSigner(request.registry.settings["secret"])
    sig_for_server = signer.sign("channelstream")
    if not six.PY2:
        sig_for_server = sig_for_server.decode("utf8")
    secret_headers = {
        "x-channelstream-secret": sig_for_server,
        "Content-Type": "application/json",
    }
    url = "http://127.0.0.1:%s%s" % (server_port, endpoint)
    response = requests.post(
        url, data=json.dumps(payload), headers=secret_headers, auth=auth
    )
    if response.status_code >= 400:
        log.error(response.text)
    response.raise_for_status()
    return response


def remove_data_from_demo_response(server_response):
    """
    Removes user info from second_channel for demo purpose
    you do not need this in real application
    :param server_response:
    :return:
    """
    channels = server_response["channels_info"]["channels"]
    second_channel = channels.get("second_channel")
    if second_channel:
        second_channel["users"] = []
    return server_response


WELCOME_MESSAGE_TEXT = """
This is a welcome message that you see upon creating connection/reconnection. 
Only you see it (it's not stored to history), and is only sent to your user.

There are 3 channels with different configurations:

- pub_chan: notifies about joins/parts, stores history, history size: 10
- notify: notifies about joins/parts, stores history, doesn't send user state change messages, history size: 50
- second_channel: doesn't notify about user presence, doesn't store history, doesn't send user state change messages
"""


def send_welcome_message(request, username):
    """
    Sends a private message to specific channel to single user
    :param request:
    :param username:
    :return:
    """
    payload = {
        "type": "message",
        "user": "system",
        "channel": "pub_chan",
        "pm_users": [username],
        "no_history": True,
        "message": {"text": WELCOME_MESSAGE_TEXT},
    }
    make_server_request(request, [payload], "/message")


@view_defaults(
    route_name="section_action", renderer="json", permission=NO_PERMISSION_REQUIRED
)
class DemoViews(object):
    def __init__(self, request):
        self.request = request
        self.request.handle_cors()
        self.request.response.headers.add("Cache-Control", "no-cache, no-store")

    @view_config(route_name="demo", renderer="templates/demo.jinja2")
    def demo(self):
        """Render demo page"""
        random_name = "anon_%s" % random.randint(1, 999999)
        return {"username": random_name}

    @view_config(match_param=["section=demo", "action=connect"], request_method="POST")
    def connect(self):
        """handle authorization of users trying to connect"""
        channels = self.request.json_body.get("channels") or []
        if channels:
            POSSIBLE_CHANNELS.intersection(channels)
        random_name = "anon_%s" % random.randint(1, 999999)
        username = self.request.json_body.get("username", random_name)
        state = self.request.json_body.get("state", {})
        payload = {
            "username": username,
            # 'conn_id': str(uuid.uuid4()),
            "channels": channels,
            "fresh_user_state": {
                "email": None,
                "status": None,
                "private": "is private",
                "bar": 1,
            },
            "user_state": state,
            "state_public_keys": ["email", "status", "bar", "color"],
            "info": {"return_public_state": True},  # return only public state
            "channel_configs": CHANNEL_CONFIGS,
        }
        result = make_server_request(self.request, payload, "/connect")
        self.request.response.status = result.status_code
        server_response = result.json()
        server_response = remove_data_from_demo_response(server_response)
        gevent.spawn_later(5, send_welcome_message, self.request, username)
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
        channels = request_data["channels"]
        POSSIBLE_CHANNELS.intersection(channels)
        payload = {
            "conn_id": request_data.get("conn_id", ""),
            "channels": request_data.get("channels", []),
            "channel_configs": CHANNEL_CONFIGS,
        }
        result = make_server_request(self.request, payload, "/subscribe")
        self.request.response.status = result.status_code
        server_response = result.json()
        server_response = remove_data_from_demo_response(server_response)
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
        server_response = remove_data_from_demo_response(server_response)
        return server_response

    @view_config(match_param=["section=demo", "action=message"], request_method="POST")
    def message(self):
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
        admin = self.request.registry.settings["admin_user"]
        admin_secret = self.request.registry.settings["admin_secret"]
        basic_auth = HTTPBasicAuth(admin, admin_secret)
        result = make_server_request(
            self.request, {}, "/admin/admin.json", auth=basic_auth
        )
        self.request.response.status = result.status_code
        return result.json()
