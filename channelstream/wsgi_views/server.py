import logging
from datetime import datetime
import gevent
import six
from gevent.queue import Queue, Empty
from pyramid.view import view_config, view_defaults
from pyramid.httpexceptions import HTTPUnauthorized
from pyramid.security import forget, NO_PERMISSION_REQUIRED
from pyramid_apispec.helpers import add_pyramid_paths
import channelstream

from channelstream import operations
from channelstream.validation import schemas
from channelstream.ext_json import json
from apispec import APISpec

log = logging.getLogger(__name__)


def get_connection_channels(connection):
    found_channels = []
    for channel in six.itervalues(channelstream.CHANNELS):
        user_conns = channel.connections.get(connection.username) or []
        if connection in user_conns:
            found_channels.append(channel.name)
    return sorted(found_channels)


class SharedUtils(object):
    def __init__(self, request):
        self.request = request

    def get_channel_info(
        self,
        req_channels=None,
        include_history=True,
        include_connections=False,
        include_users=False,
        exclude_channels=None,
        return_public_state=False,
    ):
        """
        Gets channel information for req_channels or all channels
        if req_channels is None
        :param: include_history (bool) will include message history
                for the channel
        :param: include_connections (bool) will include connection list
                for users
        :param: include_users (bool) will include user list for the channel
        :param: exclude_channels (bool) will exclude specific channels
                from info list (handy to exclude global broadcast)
        """

        if not exclude_channels:
            exclude_channels = []
        start_time = datetime.utcnow()

        json_data = {"channels": {}, "users": []}

        users_to_list = set()

        # select everything for empty list
        if req_channels is None:
            channel_instances = six.itervalues(channelstream.CHANNELS)
        else:
            channel_instances = [
                channelstream.CHANNELS[c]
                for c in req_channels
                if c in channelstream.CHANNELS
            ]

        for channel_inst in channel_instances:
            if channel_inst.name in exclude_channels:
                continue

            channel_info = channel_inst.get_info(
                include_history=include_history, include_users=include_users
            )
            json_data["channels"][channel_inst.name] = channel_info
            users_to_list.update(channel_info["users"])

        for username in users_to_list:
            user = channelstream.USERS[username]
            json_data["users"].append(
                {
                    "user": username,
                    "state": user.state
                    if not return_public_state
                    else user.public_state,
                }
            )
        log.info("info time: %s" % (datetime.utcnow() - start_time))
        return json_data

    def get_common_info(self, channels, info_config):
        """
        Return channel information based on requirements
        :param channels:
        :param info_config:
        :return:
        """
        include_history = info_config.get("include_history", True)
        include_users = info_config.get("include_users", True)
        exclude_channels = info_config.get("exclude_channels", [])
        include_connections = info_config.get("include_connections", False)
        return_public_state = info_config.get("return_public_state", False)
        channels_info = self.get_channel_info(
            channels,
            include_history=include_history,
            include_connections=include_connections,
            include_users=include_users,
            exclude_channels=exclude_channels,
            return_public_state=return_public_state,
        )
        return channels_info


@view_config(route_name="legacy_connect", request_method="POST", renderer="json")
def connect(request):
    """
    Connect view
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "Legacy API"
      summary: "connects users to the server"
      description: ""
      operationId: "connect"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        required: true
        schema:
          $ref: "#/definitions/ConnectBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
          schema:
            $ref: '#/definitions/ConnectBody'
    """
    utils = SharedUtils(request)
    schema = schemas.ConnectBodySchema(context={"request": request})
    json_body = schema.load(request.json_body).data
    channels = sorted(json_body["channels"])
    connection, user = operations.connect(
        username=json_body["username"],
        fresh_user_state=json_body["fresh_user_state"],
        state_public_keys=json_body["state_public_keys"],
        update_user_state=json_body["user_state"],
        conn_id=json_body["conn_id"],
        channels=channels,
        channel_configs=json_body["channel_configs"],
    )

    # get info config for channel information
    channels_info = utils.get_common_info(channels, json_body["info"])
    return {
        "conn_id": connection.id,
        "state": user.state,
        "username": user.username,
        "public_state": user.public_state,
        "channels": channels,
        "channels_info": channels_info,
    }


@view_config(route_name="legacy_subscribe", request_method="POST", renderer="json")
def subscribe(request, *args):
    """
    Subscribe view
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "Legacy API"
      summary: "Subscribes connection to new channels"
      description: ""
      operationId: "subscribe"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        required: true
        schema:
          $ref: "#/definitions/SubscribeBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """
    utils = SharedUtils(request)
    schema = schemas.SubscribeBodySchema(context={"request": request})
    json_body = schema.load(request.json_body).data
    connection = channelstream.CONNECTIONS.get(json_body["conn_id"])
    channels = json_body["channels"]
    channel_configs = json_body.get("channel_configs", {})
    subscribed_to = operations.subscribe(
        connection=connection, channels=channels, channel_configs=channel_configs
    )

    # get info config for channel information
    current_channels = get_connection_channels(connection)
    channels_info = utils.get_common_info(current_channels, json_body["info"])
    return {
        "channels": current_channels,
        "channels_info": channels_info,
        "subscribed_to": sorted(subscribed_to),
    }


@view_config(route_name="legacy_unsubscribe", request_method="POST", renderer="json")
def unsubscribe(request, *args):
    """
    Unsubscribe view
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "Legacy API"
      summary: "Removes connection from channels"
      description: ""
      operationId: "unsubscribe"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        required: true
        schema:
          $ref: "#/definitions/UnsubscribeBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """
    utils = SharedUtils(request)
    schema = schemas.UnsubscribeBodySchema(context={"request": request})
    json_body = schema.load(request.json_body).data
    connection = channelstream.CONNECTIONS.get(json_body["conn_id"])
    unsubscribed_from = operations.unsubscribe(
        connection=connection, unsubscribe_channels=json_body["channels"]
    )

    # get info config for channel information
    current_channels = get_connection_channels(connection)
    channels_info = utils.get_common_info(current_channels, json_body["info"])
    return {
        "channels": current_channels,
        "channels_info": channels_info,
        "unsubscribed_from": sorted(unsubscribed_from),
    }


@view_config(route_name="api_listen", request_method="GET", renderer="json")
def listen(request):
    """
    Handles long-polling connection
    :return:
    """
    config = request.registry.settings
    conn_id = request.params.get("conn_id")
    connection = channelstream.CONNECTIONS.get(conn_id)
    if not connection:
        raise HTTPUnauthorized()
    # mark the conn active
    connection.last_active = datetime.utcnow()
    # attach a queue to connection
    connection.queue = Queue()

    def yield_response():
        # for chrome issues
        # yield ' ' * 1024
        # wait for this to wake up
        messages = []
        # block for first message - wake up after a while
        try:
            messages.extend(
                connection.queue.get(timeout=config["wake_connections_after"])
            )
        except Empty:
            pass
        # get more messages if enqueued takes up total 0.25s
        while True:
            try:
                messages.extend(connection.queue.get(timeout=0.25))
            except Empty:
                break
        cb = request.params.get("callback")
        if cb:
            resp = cb + "(" + json.dumps(messages) + ")"
        else:
            resp = json.dumps(messages)
        if six.PY2:
            yield resp
        else:
            yield resp.encode("utf8")

    request.response.app_iter = yield_response()
    return request.response


@view_config(route_name="legacy_user_state", request_method="POST", renderer="json")
def user_state(request):
    """
    Sets the state of a user object
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "Legacy API"
      summary: "set the status of specific user"
      description: ""
      operationId: "user_state"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        required: true
        schema:
          $ref: "#/definitions/UserStateBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """

    schema = schemas.UserStateBodySchema(context={"request": request})
    data = schema.load(request.json_body).data
    user_inst = channelstream.USERS[data["user"]]
    # can be empty list!
    if data["state_public_keys"] is not None:
        user_inst.state_public_keys = data["state_public_keys"]
    changed = operations.change_user_state(
        user_inst=user_inst, user_state=data["user_state"]
    )
    return {
        "user_state": user_inst.state,
        "changed_state": changed,
        "public_keys": user_inst.state_public_keys,
    }


@view_config(route_name="legacy_message", request_method="POST", renderer="json")
def message(request):
    """
    Send message to channels and/or users
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "Legacy API"
      summary: "Send message to channels and/or users"
      description: ""
      operationId: "message"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        required: true
        schema:
          $ref: "#/definitions/MessageBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """

    schema = schemas.MessageBodySchema(context={"request": request}, many=True)
    data = schema.load(request.json_body).data
    for msg in data:
        if not msg.get("channel") and not msg.get("pm_users", []):
            continue
        gevent.spawn(operations.pass_message, msg, channelstream.STATS)
    return True


@view_config(
    route_name="api_disconnect", renderer="json", permission=NO_PERMISSION_REQUIRED
)
def disconnect(request):
    """
    Permanently remove connection from server
    ---
    get:
      tags:
      - "Legacy API"
      summary: "Permanently remove connection from server"
      description: ""
      operationId: "disconnect"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: query
        schema:
          type: string
        name: "conn_id"
        description: "Connection Id"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    post:
      tags:
      - "Legacy API"
      summary: "Permanently remove connection from server"
      description: ""
      operationId: "disconnect"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        schema:
          $ref: "#/definitions/DisconnectBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """
    schema = schemas.DisconnectBodySchema(context={"request": request})
    if request.method != "POST":
        payload = {"conn_id": request.GET.get("conn_id")}
    else:
        json_body = request.json_body
        payload = {"conn_id": json_body.get("conn_id")}
    data = schema.load(payload).data
    return operations.disconnect(conn_id=data["conn_id"])


@view_config(route_name="legacy_channel_config", request_method="POST", renderer="json")
def channel_config(request):
    """
    Set channel configuration
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "Legacy API"
      summary: "Set channel configuration"
      description: ""
      operationId: "channel_config"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        schema:
          $ref: "#/definitions/ChannelConfigBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """

    utils = SharedUtils(request)

    deserialized = {}
    schema = schemas.ChannelConfigSchema(context={"request": request})
    json_body = request.json_body
    for k in json_body.keys():
        deserialized[k] = schema.load(json_body[k]).data
    operations.set_channel_config(channel_configs=deserialized)
    channels_info = utils.get_channel_info(
        deserialized.keys(), include_history=False, include_users=False
    )
    return channels_info


@view_config(route_name="legacy_info", renderer="json")
def info(request):
    """
    Returns channel information
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "Legacy API"
      summary: "Returns channel information"
      description: ""
      operationId: "info"
      consumes:
      - "application/json"
      produces:
      - "application/json"
      parameters:
      - in: "body"
        name: "body"
        description: "Request JSON body"
        schema:
          $ref: "#/definitions/ChannelInfoBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """
    utils = SharedUtils(request)
    if not request.body:
        req_channels = channelstream.CHANNELS.keys()
        info_config = {
            "include_history": True,
            "include_users": True,
            "exclude_channels": [],
            "include_connections": True,
        }
    else:
        schema = schemas.ChannelInfoBodySchema(context={"request": request})
        data = schema.load(request.json_body).data
        # get info config for channel information
        info_config = data.get("info") or {}
        req_channels = info_config.get("channels", None)
        info_config["include_connections"] = info_config.get(
            "include_connections", True
        )
    print(info_config, request.json_body)
    channels_info = utils.get_common_info(req_channels, info_config)
    return channels_info


@view_defaults(route_name="action", renderer="json", permission="access")
class ServerViews(object):
    def __init__(self, request):
        self.request = request
        self.request.handle_cors()
        self.utils = SharedUtils(request)

    @view_config(
        route_name="admin", renderer="templates/admin.jinja2", permission="access"
    )
    def admin(self):
        """
        Serve admin page html
        :return:
        """
        return {}

    @view_config(route_name="admin_json", renderer="json", request_method=('POST', 'GET'), permission="access")
    def admin_json(self):
        """
        Admin json
        ---
        get:
          tags:
          - "Admin API"
          summary: "Return server information in json format for admin panel
          purposes"
          description: ""
          operationId: "admin_json"
          consumes:
          - "application/json"
          produces:
          - "application/json"
          parameters:
          - in: "body"
            name: "body"
            description: "Response info configuration"
          responses:
            422:
              description: "Unprocessable Entity"
            200:
              description: "Success"
        post:
          tags:
          - "Admin API"
          summary: "Return server information in json format for admin panel
          purposes"
          description: ""
          operationId: "admin_json"
          consumes:
          - "application/json"
          produces:
          - "application/json"
          parameters:
          - in: "body"
            name: "body"
            description: "Response info configuration"
          responses:
            422:
              description: "Unprocessable Entity"
            200:
              description: "Success"
        """

        uptime = datetime.utcnow() - channelstream.STATS["started_on"]
        uptime = str(uptime).split(".")[0]
        remembered_user_count = len(
            [user for user in six.iteritems(channelstream.USERS)]
        )
        active_users = [
            user for user in six.itervalues(channelstream.USERS) if user.connections
        ]
        unique_user_count = len(active_users)
        total_connections = sum([len(user.connections) for user in active_users])
        channels_info = self.utils.get_common_info(
            None,
            {
                "include_history": True,
                "include_users": True,
                "exclude_channels": [],
                "include_connections": True,
            },
        )
        return {
            "remembered_user_count": remembered_user_count,
            "unique_user_count": unique_user_count,
            "total_connections": total_connections,
            "total_channels": len(channelstream.CHANNELS.keys()),
            "total_messages": channelstream.STATS["total_messages"],
            "total_unique_messages": channelstream.STATS["total_unique_messages"],
            "channels": channels_info["channels"],
            "users": [user.get_info(include_connections=True) for user in active_users],
            "uptime": uptime,
        }

    # @view_config(route_name='api_explorer', permission=NO_PERMISSION_REQUIRED,
    #              renderer='templates/explorer.jinja2')
    # def api_explorer(self):
    #     return {}

    @view_config(
        route_name="openapi_spec", permission=NO_PERMISSION_REQUIRED, renderer="json"
    )
    def api_spec(self):
        """
        OpenApi 2.0 spec
        ---
        get:
          tags:
          - "OpenApi 2.0 spec"
          summary: "Return openapi spec
          purposes"
          description: ""
          operationId: "api_spec"
          consumes:
          - "application/json"
          produces:
          - "application/json"
          parameters:
          responses:
            200:
              description: "Success"
        """
        spec = APISpec(
            title="Channelstream API",
            version="0.7.0",
            plugins=["apispec.ext.marshmallow"],
        )
        spec.definition("ConnectBody", schema=schemas.ConnectBodySchema)
        spec.definition("SubscribeBody", schema=schemas.SubscribeBodySchema)
        spec.definition("UnsubscribeBody", schema=schemas.UnsubscribeBodySchema)
        spec.definition("UserStateBody", schema=schemas.UserStateBodySchema)
        spec.definition("MessageBody", schema=schemas.MessageBodySchema(many=True))
        spec.definition("DisconnectBody", schema=schemas.DisconnectBodySchema)
        spec.definition("ChannelConfigBody", schema=schemas.ChannelConfigSchema)
        spec.definition("ChannelInfoBody", schema=schemas.ChannelInfoBodySchema)

        add_pyramid_paths(spec, "legacy_connect", request=self.request)
        add_pyramid_paths(spec, "legacy_subscribe", request=self.request)
        add_pyramid_paths(spec, "legacy_unsubscribe", request=self.request)
        add_pyramid_paths(spec, "legacy_user_state", request=self.request)
        add_pyramid_paths(spec, "legacy_message", request=self.request)
        add_pyramid_paths(spec, "legacy_channel_config", request=self.request)
        add_pyramid_paths(spec, "legacy_info", request=self.request)

        add_pyramid_paths(spec, "api_listen", request=self.request)
        add_pyramid_paths(spec, "api_listen_ws", request=self.request)
        add_pyramid_paths(spec, "api_disconnect", request=self.request)

        add_pyramid_paths(spec, "admin_json", request=self.request)
        spec_dict = spec.to_dict()
        spec_dict["securityDefinitions"] = {
            "APIKeyHeader": {
                "type": "apiKey",
                "name": "X-Channelstream-Secret",
                "in": "header",
            }
        }
        return spec_dict


@view_config(context="channelstream.wsgi_views.wsgi_security:RequestBasicChallenge")
def admin_challenge(request):
    response = HTTPUnauthorized()
    response.headers.update(forget(request))
    return response
