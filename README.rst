channelstream
=============
Basic usage::

    YOUR_PYTHON_ENV/bin/channelstream


You can also see simple pyramid/angularjs demo included, open your browser and point it to following url::

    http://127.0.0.1:8000/demo

**To run the demo you will need to have the `requests` package installed in your environment**

Possible config options for the server::

    YOUR_PYTHON_ENV/bin/channelstream -h

The server can also be configured via ini files, example::

    [channelstream]
    debug = 0
    port = 8000
    demo_app_url = http://127.0.0.1
    secret = YOURSECRET
    admin_secret = YOURADMINSECRET
    allow_posting_from = 127.0.0.1,
                         x.x.x.x,
                         y.y.y.y,



Data format and endpoints
=========================

/connect?secret=YOURSECRET
--------------------------

expects a json request in form of::

    { "user": YOUR_USER_NAME,
      "conn_id": CUSTOM_UNIQUE_UID_OF_CONNECTION, # for example uuid.uuid4()
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ]
    }
   
where channels is a list of channels this connection/user should be subscribed to.

/info?secret=YOURSECRET
--------------------------

expects a json request in form of::

    { 
    "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ]
    }
   
where channels is a list of channels you want information about.
If channel list is empty server will return full list of all channels and their
information.

/disconnect
--------------------------

expects a json request in form of::

    { "conn_id": CONN_ID}

marks specific connection to be garbage collected

/message?secret=YOURSECRET
--------------------------

expects a json request in form of::

    {
    "channel": "CHAN_NAME", #optional
    "pm_users": [USER_NAME1,USER_NAME2], #optional
    "user": "NAME_OF_POSTER",
    "message": MSG_PAYLOAD
    }

When just channel is present message is public to all connections subscribed 
to the channel. When channel & pm_users is a private message is sent 
to connections subscribed to this specific channel. 
If only pm_users is present a private message is sent to all connections that are
owned by pm_users.  

/subscribe?secret=YOURSECRET
----------------------------

expects a json request in form of::

    { "channels": [ "CHAN_NAME1", "CHAN_NAMEX" ], "conn_id": "CONNECTION_ID"}


/user_status?secret=YOURSECRET
----------------------------

expects a json request in form of::

    { "user": USER_NAME, "status":STATUS_ID_INT}


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
    "message": null,
    "type": "join",
    "user": "NAME_OF_POSTER",
    "channel": "CHAN_NAME"
    }


Installation and Setup
======================

Obtain source from bitbucket and do::

    python setup.py develop