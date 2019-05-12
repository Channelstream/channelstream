import logging
from datetime import datetime

import gevent
import gevent.util
from apispec import APISpec
from apispec.ext.marshmallow import MarshmallowPlugin
from gevent.queue import Queue, Empty
from pyramid.httpexceptions import HTTPUnauthorized, HTTPFound
from pyramid.security import remember, forget, NO_PERMISSION_REQUIRED
from pyramid.view import view_config, view_defaults
from pyramid_apispec.helpers import add_pyramid_paths

from channelstream import operations, utils, patched_json as json, __version__
from channelstream.server_state import get_state, STATS
from channelstream.validation import schemas

log = logging.getLogger(__name__)


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
        server_state = get_state()
        if not exclude_channels:
            exclude_channels = []
        start_time = datetime.utcnow()

        json_data = {"channels": {}, "users": []}

        users_to_list = set()

        # select everything for empty list
        if req_channels is None:
            channel_instances = server_state.channels.values()
        else:
            channel_instances = [
                server_state.channels[c]
                for c in req_channels
                if c in server_state.channels
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
            user = server_state.users[username]
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


@view_config(route_name="connect", request_method="POST", renderer="json")
def connect(request):
    """
    Connect view
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
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
    shared_utils = SharedUtils(request)
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
    channels_info = shared_utils.get_common_info(channels, json_body["info"])

    return {
        "conn_id": connection.id,
        "state": user.state,
        "username": user.username,
        "public_state": user.public_state,
        "channels": channels,
        "channels_info": channels_info,
    }


@view_config(route_name="subscribe", request_method="POST", renderer="json")
def subscribe(request):
    """
    Subscribe view
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
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
    server_state = get_state()
    shared_utils = SharedUtils(request)
    schema = schemas.SubscribeBodySchema(context={"request": request})
    json_body = schema.load(request.json_body).data
    connection = server_state.connections.get(json_body["conn_id"])
    channels = json_body["channels"]
    channel_configs = json_body.get("channel_configs", {})
    subscribed_to = operations.subscribe(
        connection=connection, channels=channels, channel_configs=channel_configs
    )

    # get info config for channel information
    current_channels = connection.channels
    channels_info = shared_utils.get_common_info(current_channels, json_body["info"])
    return {
        "channels": current_channels,
        "channels_info": channels_info,
        "subscribed_to": sorted(subscribed_to),
    }


@view_config(route_name="unsubscribe", request_method="POST", renderer="json")
def unsubscribe(request):
    """
    Unsubscribe view
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
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
    server_state = get_state()
    shared_utils = SharedUtils(request)
    schema = schemas.UnsubscribeBodySchema(context={"request": request})
    json_body = schema.load(request.json_body).data
    connection = server_state.connections.get(json_body["conn_id"])
    unsubscribed_from = operations.unsubscribe(
        connection=connection, unsubscribe_channels=json_body["channels"]
    )

    # get info config for channel information
    current_channels = connection.channels
    channels_info = shared_utils.get_common_info(current_channels, json_body["info"])
    return {
        "channels": current_channels,
        "channels_info": channels_info,
        "unsubscribed_from": sorted(unsubscribed_from),
    }


@view_config(
    route_name="api_listen",
    request_method="GET",
    renderer="json",
    permission=NO_PERMISSION_REQUIRED,
)
def listen(request):
    """
    Handles long polling connections
    ---
    get:
      tags:
      - "Client API"
      summary: "Handles long polling connections"
      description: ""
      operationId: "listen"
      produces:
      - "application/json"
      responses:
        200:
          description: "Success"
    """
    server_state = get_state()
    config = request.registry.settings
    conn_id = utils.uuid_from_string(request.params.get("conn_id"))
    connection = server_state.connections.get(conn_id)
    if not connection:
        raise HTTPUnauthorized()
    # attach a queue to connection
    connection.queue = Queue()
    connection.deliver_catchup_messages()
    request.response.app_iter = yield_response(request, connection, config)
    return request.response


def yield_response(request, connection, config):
    messages = await_data(connection, config)
    connection.mark_activity()
    cb = request.params.get("callback")
    if cb:
        resp = cb + "(" + json.dumps(messages) + ")"
    else:
        resp = json.dumps(messages)
    yield resp.encode("utf8")


def await_data(connection, config):
    messages = []
    # block for first message - wake up after a while
    try:
        messages.extend(connection.queue.get(timeout=config["wake_connections_after"]))
    except Empty:
        pass
    # get more messages if enqueued takes up total 0.25
    while True:
        try:
            messages.extend(connection.queue.get(timeout=0.25))
        except Empty:
            break
    return messages


@view_config(route_name="user_state", request_method="POST", renderer="json")
def user_state(request):
    """
    Sets the state of a user object
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
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
    server_state = get_state()
    schema = schemas.UserStateBodySchema(context={"request": request})
    data = schema.load(request.json_body).data
    user_inst = server_state.users[data["user"]]
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


def shared_messages(request):
    server_state = get_state()
    schema = schemas.MessageBodySchema(context={"request": request}, many=True)
    data = schema.load(request.json_body).data
    data = [m for m in data if m.get("channel") or m.get("pm_users")]
    for msg in data:
        gevent.spawn(operations.pass_message, msg, server_state.stats)
    return list(data)


# prepare v1 version
# @view_config(route_name="api_v1_messages", request_method="POST", renderer="json")
def messages_post(request):
    """
    Send message to channels and/or users
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "V1 API (future stable)"
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
          $ref: "#/definitions/MessagesBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """
    return shared_messages(request)


@view_config(route_name="message", request_method="POST", renderer="json")
def message(request):
    """
    Send message to channels and/or users
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
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
          $ref: "#/definitions/MessagesBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """
    return shared_messages(request)


@view_config(route_name="message", request_method="PATCH", renderer="json")
def messages_patch(request):
    """
    Edit existing message in history and emit changes
    ---
    patch:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
      summary: "Edit existing message in history and emit changes"
      description: ""
      operationId: "edit_messages"
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
          $ref: "#/definitions/MessageEditBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """

    schema = schemas.MessageEditBodySchema(context={"request": request}, many=True)
    data = schema.load(request.json_body).data
    for msg in data:
        gevent.spawn(operations.edit_message, msg)
    return data


@view_config(route_name="message", request_method="DELETE", renderer="json")
def messages_delete(request):
    """
    Delete message from history and emit changes
    ---
    delete:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
      summary: "Delete message from history and  emit changes"
      description: ""
      operationId: "messages_delete"
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
          $ref: "#/definitions/MessagesDeleteBody"
      responses:
        422:
          description: "Unprocessable Entity"
        200:
          description: "Success"
    """

    schema = schemas.MessagesDeleteBodySchema(context={"request": request}, many=True)
    data = schema.load(request.json_body).data
    for msg in data:
        gevent.spawn(operations.delete_message, msg)
    return data


@view_config(
    route_name="api_disconnect", renderer="json", permission=NO_PERMISSION_REQUIRED
)
def disconnect(request):
    """
    Permanently remove connection from server
    ---
    get:
      tags:
      - "Client API"
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
      - "Client API"
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


@view_config(route_name="channel_config", request_method="POST", renderer="json")
def channel_config(request):
    """
    Set channel configuration
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
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

    shared_utils = SharedUtils(request)

    deserialized = {}
    schema = schemas.ChannelConfigSchema(context={"request": request})
    json_body = request.json_body
    for k in json_body.keys():
        deserialized[k] = schema.load(json_body[k]).data
    operations.set_channel_config(channel_configs=deserialized)
    channels_info = shared_utils.get_channel_info(
        deserialized.keys(), include_history=False, include_users=False
    )
    return channels_info


@view_config(route_name="info", renderer="json")
def info(request):
    """
    Returns channel information
    ---
    post:
      security:
        - APIKeyHeader: []
      tags:
      - "API"
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
    server_state = get_state()
    shared_utils = SharedUtils(request)
    if not request.body:
        req_channels = server_state.channels.keys()
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
    channels_info = shared_utils.get_common_info(req_channels, info_config)
    return channels_info


@view_defaults(route_name="action", renderer="json", permission="admin")
class ServerViews(object):
    def __init__(self, request):
        self.request = request
        self.utils = SharedUtils(request)

    @view_config(route_name="admin", renderer="templates/admin.jinja2")
    def admin(self):
        """
        Serve admin page html
        :return:
        """
        return {}

    @view_config(
        route_name="admin_action", match_param=("action=debug",), renderer="string"
    )
    def admin_debug(self):
        return "\n".join(gevent.util.format_run_info())

    @view_config(
        route_name="admin_action",
        match_param=("action=sign_in",),
        renderer="templates/sign_in.jinja2",
        permission=NO_PERMISSION_REQUIRED,
    )
    def admin_sign_in(self):
        if self.request.method == "POST":
            admin_user = self.request.registry.settings["admin_user"]
            admin_secret = self.request.registry.settings["admin_secret"]
            username = self.request.POST.get("username", "").strip()
            password = self.request.POST.get("password", "").strip()
            if username == admin_user and password == admin_secret:
                headers = remember(self.request, admin_user)
                url = self.request.route_url("admin")
                return HTTPFound(url, headers=headers)
            else:
                # make potential brute forcing non-feasible
                gevent.sleep(0.5)
        return {}

    @view_config(
        route_name="admin_action",
        match_param=("action=sign_out",),
        renderer="string",
        permission=NO_PERMISSION_REQUIRED,
    )
    def admin_sign_out(self):
        headers = forget(self.request)
        url = self.request.route_url("admin_action", action="sign_in")
        return HTTPFound(url, headers=headers)

    @view_config(
        route_name="admin_json", renderer="json", request_method=("POST", "GET")
    )
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
        server_state = get_state()
        uptime = datetime.utcnow() - STATS["started_on"]
        uptime = str(uptime).split(".")[0]
        remembered_user_count = len([user for user in server_state.users.items()])
        active_users = [
            user for user in server_state.users.values() if user.connections
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
            "total_channels": len(server_state.channels.keys()),
            "total_messages": server_state.stats["total_messages"],
            "total_unique_messages": server_state.stats["total_unique_messages"],
            "channels": channels_info["channels"],
            "users": [user.get_info(include_connections=True) for user in active_users],
            "uptime": uptime,
            "version": str(__version__),
        }

    @view_config(route_name="openapi_spec", renderer="json")
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
            openapi_version="2.0.0",
            plugins=(MarshmallowPlugin(),),
        )
        spec.components.schema("ConnectBody", schema=schemas.ConnectBodySchema)
        spec.components.schema("SubscribeBody", schema=schemas.SubscribeBodySchema)
        spec.components.schema("UnsubscribeBody", schema=schemas.UnsubscribeBodySchema)
        spec.components.schema("UserStateBody", schema=schemas.UserStateBodySchema)
        spec.components.schema(
            "MessagesBody", schema=schemas.MessageBodySchema(many=True)
        )
        spec.components.schema("MessageBody", schema=schemas.MessageBodySchema())
        spec.components.schema(
            "MessageEditBody", schema=schemas.MessageEditBodySchema(many=True)
        )
        spec.components.schema(
            "MessagesDeleteBody", schema=schemas.MessagesDeleteBodySchema(many=True)
        )
        spec.components.schema("DisconnectBody", schema=schemas.DisconnectBodySchema)
        spec.components.schema("ChannelConfigBody", schema=schemas.ChannelConfigSchema)
        spec.components.schema("ChannelInfoBody", schema=schemas.ChannelInfoBodySchema)

        # api
        add_pyramid_paths(spec, "connect", request=self.request)
        add_pyramid_paths(spec, "subscribe", request=self.request)
        add_pyramid_paths(spec, "unsubscribe", request=self.request)
        add_pyramid_paths(spec, "user_state", request=self.request)
        add_pyramid_paths(spec, "message", request=self.request)
        add_pyramid_paths(spec, "channel_config", request=self.request)
        add_pyramid_paths(spec, "info", request=self.request)

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
