import json
import logging
import random

import requests
import six

from flask import Flask, render_template, request
from itsdangerous import TimestampSigner

log = logging.getLogger(__name__)
app = Flask(__name__)


def make_server_request(payload, endpoint, auth=None, method="post"):
    """
    Makes a json request to channelstream server endpoint signing the request and sending the payload
    """
    server_port = 8000
    signer = TimestampSigner("secret")
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

    return response


@app.route("/")
def demo():
    """ Render demo page """
    random_name = "anon_%s" % random.randint(1, 999999)
    return render_template("index.html", username=random_name)


@app.route("/connect", methods=["POST"])
def connect():
    """ Connect to sample channel """
    data = json.loads(request.data.decode("utf-8"))
    random_name = "anon_%s" % random.randint(1, 999999)
    username = data.get("username", random_name)
    payload = {"username": username, "channels": ["notify"]}
    result = make_server_request(payload, "/connect")
    return result.text


@app.route("/message", methods=["POST"])
def message_post():
    """ Send message to channel/users """
    request_data = json.loads(request.data.decode("utf-8"))
    payload = {
        "type": "message",
        "user": request_data.get("user", "system"),
        "channel": "notify",
        "message": {"value": request_data.get("message")},
    }
    result = make_server_request([payload], "/message")
    return result.text
