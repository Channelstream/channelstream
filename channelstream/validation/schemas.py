from datetime import datetime

import marshmallow
from marshmallow import validate, fields

from channelstream.validation import (
    BackportedDict,
    ChannelstreamSchema,
    gen_uuid,
    validate_connection_id,
    validate_username,
    UserStateField,
)


class ChannelConfigSchema(ChannelstreamSchema):
    notify_presence = fields.Boolean(
        missing=False, description="Should presence operations emit notifications"
    )
    store_history = fields.Boolean(
        missing=False, description="Should store history messages"
    )
    history_size = fields.Integer(
        missing=10,
        validate=[validate.Range(min=0)],
        description="How many messages should be stored",
    )
    broadcast_presence_with_user_lists = fields.Boolean(
        missing=False,
        description="should currently connected users be sent on connection requests",
    )
    notify_state = fields.Boolean(
        missing=False, description="Should emit public state changes"
    )
    store_frames = fields.Boolean(
        missing=True, description="Should store catchup frames"
    )


class InfoResolutionSchema(ChannelstreamSchema):
    include_history = fields.Boolean(missing=True)
    include_users = fields.Boolean(missing=True)
    channels = fields.List(fields.String(validate=validate.Length(min=1, max=256)))
    exclude_channels = fields.List(
        fields.String(validate=validate.Length(min=1, max=256))
    )
    include_connections = fields.Boolean(missing=False)
    return_public_state = fields.Boolean(missing=False)


class ChannelInfoBodySchema(ChannelstreamSchema):
    info = fields.Nested(InfoResolutionSchema, required=True)


class ConnectBodySchema(ChannelstreamSchema):
    username = fields.String(
        required=True,
        validate=validate.Length(min=1, max=512),
        description="Identifier for user, will be used for other operations",
    )

    conn_id = fields.UUID(
        missing=gen_uuid,
        description="Connection identifier used for broadcast listening",
    )

    channels = fields.List(
        fields.String(validate=validate.Length(min=1, max=256)),
        description="List of channels user should be subscribed to, "
        "the chnnels will be auto created upon connection",
        missing=lambda: [],
    )

    state_public_keys = fields.List(
        fields.String(description="", validate=validate.Length(min=1, max=256)),
        missing=lambda: [],
        description="What state keys should be visible/emitted to other users",
    )

    fresh_user_state = BackportedDict(
        missing=lambda: {},
        values=UserStateField(allow_none=True),
        keys=fields.String(),
        description="Default user state if user object is not in server memory",
    )
    user_state = BackportedDict(
        missing=lambda: {},
        values=UserStateField(allow_none=True),
        keys=fields.String(),
        description="Update user state to values in this dictionary, "
        "values not present in dict are kept intact, valid values are: "
        "string, int, float and boolean",
    )
    channel_configs = BackportedDict(
        missing=lambda: {},
        values=fields.Nested(ChannelConfigSchema()),
        keys=fields.String(),
        description="Sets configuration for newly created channels "
        "in form of channelName:ChannelConfigBody",
    )
    info = fields.Nested(
        InfoResolutionSchema(),
        missing=lambda: {},
        description="Controls how much information should be returned in response",
    )


class SubscribeBodySchema(ChannelstreamSchema):
    conn_id = fields.UUID(required=True, validate=[validate_connection_id])

    channels = fields.List(
        fields.String(validate=validate.Length(min=1, max=256)),
        required=True,
        validate=validate.Length(min=1),
        description="List of channels user should be subscribed to",
    )
    info = fields.Nested(InfoResolutionSchema(), missing=lambda: {})

    channel_configs = BackportedDict(
        missing=lambda: {},
        values=fields.Nested(ChannelConfigSchema()),
        keys=fields.String(),
        description="Sets configuration for newly created channels "
        "in form of channelName:ChannelConfigBody",
    )

    @marshmallow.pre_load
    def get_connection(self, in_data):
        in_data.setdefault("conn_id", self.context["request"].GET.get("conn_id"))
        return in_data


class UnsubscribeBodySchema(SubscribeBodySchema):
    pass


class UserStateBodySchema(ChannelstreamSchema):
    user = fields.String(
        required=True, validate=[validate.Length(min=1, max=512), validate_username]
    )

    user_state = BackportedDict(
        missing=lambda: {},
        values=UserStateField(allow_none=True),
        keys=fields.String(),
        description="Update user state to values in this dictionary, "
        "values not present in dict are kept intact, valid values are: "
        "string, int, float and boolean",
    )
    state_public_keys = fields.List(
        fields.String(validate=validate.Length(min=1, max=256)),
        missing=None,
        description="What state keys should be visible/emitted to other users",
    )


class PayloadDeliveryInfo(ChannelstreamSchema):
    pm_users = fields.List(
        fields.String(validate=validate.Length(min=1, max=512)),
        missing=lambda: [],
        description="Which users should get the message, either globally or in channel context",
    )
    exclude_users = fields.List(
        fields.String(validate=validate.Length(min=1, max=512)),
        missing=lambda: [],
        description="Which users should not have the message delivered, preceeds pm_users",
    )
    channel = fields.String(
        validate=validate.Length(min=1, max=256),
        missing=None,
        description="What channel should the message be delivered to",
    )
    no_history = fields.Boolean(
        missing=False, description="Should store the message in history"
    )


class MessageBodySchema(PayloadDeliveryInfo, ChannelstreamSchema):
    uuid = fields.UUID(
        default=gen_uuid, missing=gen_uuid, description="Identifier of emitted message"
    )
    timestamp = fields.DateTime(
        missing=lambda: datetime.utcnow().isoformat(),
        description="Registered timestamp of message",
    )
    user = fields.String(
        required=True,
        validate=validate.Length(min=1, max=512),
        description="Sender identifier",
    )
    message = fields.Dict(description="Message payload, can hold other keys")

    @marshmallow.post_load()
    def _add_unknown(self, data):
        data["edited"] = None
        return data


class MessageEditBodySchema(MessageBodySchema):
    uuid = fields.UUID(
        required=True, description="Identifier of message that is being edited"
    )
    timestamp = fields.DateTime()
    user = fields.String(validate=validate.Length(min=1, max=512))
    message = fields.Dict()
    edited = fields.DateTime(missing=lambda: datetime.utcnow().isoformat())

    @marshmallow.post_load()
    def _add_unknown(self, data):
        return data


class MessagesDeleteBodySchema(PayloadDeliveryInfo, ChannelstreamSchema):
    uuid = fields.UUID(
        required=True,
        description="Identifier of message that should be deleted from history",
    )


class DisconnectBodySchema(ChannelstreamSchema):
    conn_id = fields.UUID(required=True)
