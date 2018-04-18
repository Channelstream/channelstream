import uuid

import marshmallow
from marshmallow import validate, fields
from channelstream import doc_utils

def gen_uuid():
    return str(uuid.uuid4())


class ChannelstreamSchema(marshmallow.Schema):
    class Meta:
        strict = True
        ordered = True
        preserve = True


class ConnectBodySchema(ChannelstreamSchema):
    username = fields.String(
        required=True,
        validate=validate.Length(min=1, max=512))

    conn_id = fields.String(
        missing=gen_uuid,
        validate=validate.Length(min=1, max=256))

    channels = fields.List(fields.String(
        missing=lambda: [],
        description='List of channels user should be subscribed to',
        validate=validate.Length(min=1, max=256)))

    state_public_keys = fields.List(fields.String(
        many=True,
        missing=lambda: [],
        description='',
        validate=validate.Length(min=1, max=256)))

    state_public_keys = fields.List(fields.String(
        many=True,
        missing=lambda: [],
        description='',
        validate=validate.Length(min=1, max=512)))

    fresh_user_state = fields.Dict(missing=lambda: {})
    user_state = fields.Dict(missing=lambda: {})
    channel_configs = fields.Dict(missing=lambda: {})
    info = fields.Dict(missing=lambda: {})


class SubscribeBodySchema(ChannelstreamSchema):
    conn_id = fields.String(
        missing=gen_uuid,
        validate=validate.Length(min=1, max=256))

    channels = fields.List(fields.String(
        description='List of channels user should be subscribed to',
        validate=validate.Length(min=1, max=256)),
        required=True,
        validate=validate.Length(min=1))
    info = fields.Dict(missing=lambda: {})


class UnsubscribeBodySchema(SubscribeBodySchema):
    pass
