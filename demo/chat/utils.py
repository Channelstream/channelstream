import json

import requests
import six
from itsdangerous import TimestampSigner


def make_server_request(request, payload, endpoint, auth=None, method="post"):
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
    response = getattr(requests, method)(
        url, data=json.dumps(payload), headers=secret_headers, auth=auth
    )
    if response.status_code >= 400:
        log.error(response.text)
    response.raise_for_status()
    return response


def send_welcome_message(request, username):
    """
    Sends a private message to specific channel to single user
    :param request:
    :param username:
    :return:
    """
    WELCOME_MESSAGE_TEXT = """
    This is a welcome message that you see upon creating connection/reconnection.
    Only you see it (it's not stored to history), and is only sent to your user.

    There are 3 channels with different configurations:

    - pub_chan: notifies about joins/parts, stores history, history size: 10
    - notify: notifies about joins/parts, stores history, doesn't send user state change messages, history size: 50
    - second_channel: doesn't notify about user presence, doesn't store history, doesn't send user state change messages
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
