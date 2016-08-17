channelstream
=============

This is a websocket-based communication server for python.

Basic usage::

    YOUR_PYTHON_ENV/bin/channelstream -i filename.ini


You can also see simple pyramid/angularjs demo included, open your browser and point it to following url::

    http://127.0.0.1:8000/demo

**To run the demo you will need to have the `requests` package installed in your environment**

Possible config options for the server::

    YOUR_PYTHON_ENV/bin/channelstream -h


The server can also be configured via ini files (channelstream -i filename), example::

    [channelstream]
    debug = 0
    port = 8000
    demo_app_url = http://127.0.0.1
    secret = YOURSECRET
    admin_secret = YOURADMINSECRET
    allow_posting_from = 127.0.0.1,
                         x.x.x.x,
                         y.y.y.y,



** USAGE **

Refer to channelstream/wsgi_views/demo.py for example usage.

** Security model **

To send information client interacts only with your normal www application.
Your app handled authentication and processing messages from client, then passed
them as signed message to channelstream server for broadcast.

websocket client -> webapp (security and transformation happens here) -> REST call to socket server -> broadcast to other clients

This model is easy to implement, secure, easy to scale and allows all kind of
languages/apps/work queues to interact with socket server.

All messages need to be signed with a HMAC of destination endpoint ::

    import requests
    from itsdangerous import TimestampSigner
    signer = TimestampSigner(request.registry.settings['secret'])
    sig_for_server = signer.sign('/connect')
    secret_headers = {'x-channelstream-secret': sig_for_server,
                      'x-channelstream-endpoint': endpoint,
                      'Content-Type': 'application/json'}
    response = requests.post(url, data=json.dumps(payload),
                             headers=secret_headers).json()

The function accepts endpoint in form of '/messages' if you want to send a message
 to users. This will be validated on socketio server side.



Data format and endpoints
=========================

/connect
--------------------------

expects a json request in form of::

    {
    "username": YOUR_username,
    "conn_id": CUSTOM_UNIQUE_UID_OF_CONNECTION, # for example uuid.uuid4()
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ],
    "channel_configs": {
        "CHAN_NAME1": {
            "notify_presence": true, 
            "history_size": 50,
            "store_history": true,
            "broadcast_presence_with_user_lists": true,
            }}, # channel_configs key is optional
    "fresh_user_state": {"avatar":"foo", "bar":1}}, # if user object is not found set this state on newly created user object (optional)
    "user_state": {"bar":2}} # update user object state with keys from this dictionary (optional),
    "state_public_keys": ["avatar", "bar"], # whitelist state keys to be sent back to clients inside presence payloads (optional)
    "info": {
        "exclude_channels": ["broadcast"],
        "include_history": true,
        "include_users": true,
        "include_connections": false
    } # information config for the server response (optional)
    }
   
where `channels` is a list of channels this connection/user should be subscribed to.
`channel_configs` is optional dictionary of defaults used for channel creation.

Keys used in `channel_configs` to describe channel behavior (and their defaults):

* notify_presence = False
* broadcast_presence_with_user_lists = False
* store_history = False
* history_size = 10


/info
--------------------------

expects a json request in form of::

    { 
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ],
    "info": {
        "exclude_channels": ["broadcast"],
        "include_history": true,
        "include_users": true,
        "include_connections": false
    } # information config for the server response
    }
   
where channels is a list of channels you want information about.
If channel list is empty server will return full list of all channels and their
information.


/disconnect
--------------------------

expects a json request in form of::

    { "conn_id": CONN_ID}

marks specific connection to be garbage collected


/message
--------------------------

expects a json request in form of list of messages::

    [{
    "channel": "CHAN_NAME", #optional if pm_users present
    "pm_users": [username1,username2], #optional if channel present
    "exclude_users": [username1,username2], #optional do not send to following users on channel
    "user": "NAME_OF_POSTER",
    "message": MSG_PAYLOAD
    }]

When just channel is present message is public to all connections subscribed 
to the channel. When channel & pm_users is a private message is sent 
to connections subscribed to this specific channel. 
If only pm_users is present a private message is sent to all connections that are
owned by pm_users.  


/subscribe
----------------------------

expects a json request in form of::

    {
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ],
    "channel_configs": {"CHAN_NAME1": {"notify_presence": true, "history_size": 50}}, # channel_configs key is optional
    "conn_id": "CONNECTION_ID"}

/unsubscribe
----------------------------

expects a json request in form of::

    {
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ],
    "conn_id": "CONNECTION_ID"}


/user_state
----------------------------

expects a json request in form of::

    {
    "user": username,
    "user_state":{"bar":2},
    "state_public_keys": ["avatar", "bar"]
    }

Listening endpoints
-------------------

for websockets:

    /ws?conn_id=CONNID

for long polling:

    /listen?conn_id=CONNID


Responses to js client
----------------------

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


Installation and Setup
======================

Obtain source from github and do::

    python setup.py develop
