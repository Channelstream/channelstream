# Channelstream

[![Build Status]](https://travis-ci.org/Channelstream/channelstream)

This is a websocket-based communication server for python applications,
your applications communicate with it via simple JSON REST API.

Visit http://channelstream.org for more information.

## Installation and Setup

Obtain source from github and do:

    YOUR_PYTHON_ENV/bin/pip install channelstream

Generate new configuration:

    YOUR_PYTHON_ENV/bin/channelstream_utils make_config -o config.ini

Start the server:

    YOUR_PYTHON_ENV/bin/channelstream -i config.ini

The server can be configured via ini files (channelstream -i filename), example:


## Demos

This repository provides demonstrative applications on how to connect with the server
and send information to clients.

You have a simple notification demo built on flask:

    cd demo/notification/
    YOUR_PYTHON_ENV/bin/pip install flask
    YOUR_PYTHON_ENV/bin/flask run

Now you can open multiple browser windows to http://127.0.0.1:5000/ and test notifications.

There is also more complex chat application demo included, it showcases
multiple channel subscriptions, message edits and user state changing.

    YOUR_PYTHON_ENV/bin/python demo/chat/app.py

Open your browser and point it to following url:

    http://127.0.0.1:6543

To run the demo you will need to have the `requests` package installed in your environment.

### Security and communication model

Channelstream provides API explorer that you can use to interact with various
endpoints, it is available by default under http://127.0.0.1:8000/api-explorer.

To send information client interacts only with your normal www application.
Your app handled authentication and processing messages from client, then passed
them as signed message to channelstream server for broadcast.

websocket client -> webapp (security and transformation happens here) -> REST call to socket server -> broadcast to other clients

This model is easy to implement, secure, easy to scale and allows all kind of
languages/apps/work queues to interact with socket server.

All messages need to be signed with a HMAC of destination endpoint ::

    import requests
    from itsdangerous import TimestampSigner
    signer = TimestampSigner(SERVER_SECRET)
    sig_for_server = signer.sign('/connect')
    secret_headers = {'x-channelstream-secret': sig_for_server,
                      'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload),
                             headers=secret_headers).json()

## Data format and endpoints

Please consult API Explorer (http://127.0.0.1:8000/api-explorer) for in depth information
about endpoints.

Some examples:

* /connect **POST** connects users to the server
* /subscribe **POST** Subscribes connection to new channels
* /unsubscribe **POST** Removes connection from channels
* /user_state **POST** set the state of specific user
* /message **POST** Send message to channels and/or users
* /message **DELETE** Delete message from history and emit changes
* /message **PATCH** Edit existing message in history and emit changes
* /channel_config **POST** Set channel configuration
* /info **POST** Returns channel information

Client API

* /ws **GET** Handles websocket connections
* /listen **GET** Handles long polling connections
* /disconnect **GET** Permanently remove connection from server
* /disconnect **POST** Permanently remove connection from server


Admin API

* /admin/admin.json **GET** Return server information in json format for admin panel purposes
* /admin/admin.json **POST** Return server information in json format for admin panel purposes

### Responses to js client

Responses to client are in form of **list** containing **objects**:

examples:

**new message** ::

    {
    "date": "2011-09-15T11:36:18.471862",
    "message": MSG_PAYLOAD,
    "type": "message",
    "user": "NAME_OF_POSTER",
    "channel": "CHAN_NAME"
    }

**presence info** ::

    {
    "date": "2011-09-15T11:43:47.434905",
    "message": {"action":"joined/parted"},
    "type": "presence",
    "user": "NAME_OF_POSTER",
    "channel": "CHAN_NAME"
    }

Currently following message types are emited: `message`, `message:edit`,
`message:delete`, `presence`, `user_state_change`.

[Build Status]: https://travis-ci.org/Channelstream/channelstream.svg?branch=master
