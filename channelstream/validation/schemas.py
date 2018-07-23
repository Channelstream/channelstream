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
    notify_presence = fields.Boolean(missing=False)
    store_history = fields.Boolean(missing=False)
    history_size = fields.Integer(missing=10, validate=[validate.Range(min=0)])
    broadcast_presence_with_user_lists = fields.Boolean(missing=False)
    notify_state = fields.Boolean(missing=False)
    store_frames = fields.Boolean(missing=True)


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
    username = fields.String(required=True, validate=validate.Length(min=1, max=512))

    conn_id = fields.UUID(missing=gen_uuid)

    channels = fields.List(
        fields.String(validate=validate.Length(min=1, max=256)),
        description="List of channels user should be subscribed to",
        missing=lambda: [],
    )

    state_public_keys = fields.List(
        fields.String(description="", validate=validate.Length(min=1, max=256)),
        missing=lambda: [],
    )

    fresh_user_state = BackportedDict(
        missing=lambda: {}, values=UserStateField(allow_none=True), keys=fields.String()
    )
    user_state = BackportedDict(
        missing=lambda: {}, values=UserStateField(allow_none=True), keys=fields.String()
    )
    channel_configs = BackportedDict(
        missing=lambda: {},
        values=fields.Nested(ChannelConfigSchema()),
        keys=fields.String(),
    )
    info = fields.Nested(InfoResolutionSchema(), missing=lambda: {})


class SubscribeBodySchema(ChannelstreamSchema):
    conn_id = fields.UUID(required=True, validate=[validate_connection_id])

    channels = fields.List(
        fields.String(
            description="List of channels user should be subscribed to",
            validate=validate.Length(min=1, max=256),
        ),
        required=True,
        validate=validate.Length(min=1),
    )
    info = fields.Nested(InfoResolutionSchema(), missing=lambda: {})

    channel_configs = BackportedDict(
        missing=lambda: {},
        values=fields.Nested(ChannelConfigSchema()),
        keys=fields.String(),
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
        missing=lambda: {}, values=UserStateField(allow_none=True), keys=fields.String()
    )
    state_public_keys = fields.List(
        fields.String(validate=validate.Length(min=1, max=256)), missing=None
    )


class PayloadDeliveryInfo(ChannelstreamSchema):
    pm_users = fields.List(
        fields.String(validate=validate.Length(min=1, max=512)), missing=lambda: []
    )
    exclude_users = fields.List(
        fields.String(validate=validate.Length(min=1, max=512)), missing=lambda: []
    )
    channel = fields.String(validate=validate.Length(min=1, max=256), missing=None)
    no_history = fields.Boolean(missing=False)


class MessageBodySchema(PayloadDeliveryInfo, ChannelstreamSchema):
    uuid = fields.UUID(default=gen_uuid, missing=gen_uuid)
    timestamp = fields.DateTime(missing=lambda: datetime.utcnow().isoformat())
    user = fields.String(required=True, validate=validate.Length(min=1, max=512))
    message = fields.Dict()

    @marshmallow.post_load()
    def _add_unknown(self, data):
        data["edited"] = None
        return data


class MessageEditBodySchema(MessageBodySchema):
    uuid = fields.UUID(required=True)
    timestamp = fields.DateTime()
    user = fields.String(validate=validate.Length(min=1, max=512))
    message = fields.Dict()
    edited = fields.DateTime(missing=lambda: datetime.utcnow().isoformat())


class MessagesDeleteBodySchema(PayloadDeliveryInfo, ChannelstreamSchema):
    uuid = fields.UUID(required=True)


class DisconnectBodySchema(ChannelstreamSchema):
    conn_id = fields.UUID(
        required=True,
        validate=[validate.Length(min=1, max=256), validate_connection_id],
    )
