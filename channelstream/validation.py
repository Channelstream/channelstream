import uuid

import channelstream
import marshmallow
from marshmallow import validate, fields


def gen_uuid():
    return str(uuid.uuid4()).replace('-', '')


def validate_connection_id(conn_id):
    if conn_id not in channelstream.CONNECTIONS:
        raise marshmallow.ValidationError('Unknown connection')


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
        description='List of channels user should be subscribed to',
        validate=validate.Length(min=1, max=256)),
        missing=lambda: [])

    state_public_keys = fields.List(fields.String(
        many=True,
        description='',
        validate=validate.Length(min=1, max=256)),
        missing=lambda: [])

    fresh_user_state = fields.Dict(missing=lambda: {})
    user_state = fields.Dict(missing=lambda: {})
    channel_configs = fields.Dict(missing=lambda: {})
    info = fields.Dict(missing=lambda: {})


class SubscribeBodySchema(ChannelstreamSchema):
    conn_id = fields.String(
        required=True,
        validate=[validate.Length(min=1, max=256),
                  validate_connection_id])

    channels = fields.List(fields.String(
        description='List of channels user should be subscribed to',
        validate=validate.Length(min=1, max=256)),
        required=True,
        validate=validate.Length(min=1))
    info = fields.Dict(missing=lambda: {})

    @marshmallow.pre_load
    def get_connection(self, in_data):
        in_data.setdefault('conn_id',
                           self.context['request'].GET.get('conn_id'))
        return in_data

class UnsubscribeBodySchema(SubscribeBodySchema):
    pass
