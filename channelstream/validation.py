import uuid
from datetime import datetime

import channelstream
import marshmallow
from marshmallow import validate, fields


def gen_uuid():
    return str(uuid.uuid4()).replace('-', '')


def validate_connection_id(conn_id):
    if conn_id not in channelstream.CONNECTIONS:
        raise marshmallow.ValidationError('Unknown connection')


def validate_username(username):
    if username not in channelstream.USERS:
        raise marshmallow.ValidationError('Unknown user')


class ChannelstreamSchema(marshmallow.Schema):
    class Meta:
        strict = True
        ordered = True


class ConnectBodySchema(ChannelstreamSchema):
    username = fields.String(
        required=True,
        validate=validate.Length(min=1, max=512))

    conn_id = fields.String(
        missing=gen_uuid,
        validate=validate.Length(min=1, max=256))

    channels = fields.List(fields.String(
        validate=validate.Length(min=1, max=256)),
        description='List of channels user should be subscribed to',
        missing=lambda: [])

    state_public_keys = fields.List(fields.String(
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
    @marshmallow.post_load(pass_original=True)
    def _add_unknown(self, data, original):
        return add_missing_fields(data, original, self.fields)


class UserStateBodySchema(ChannelstreamSchema):
    user = fields.String(
        required=True,
        validate=[validate.Length(min=1, max=512),
                  validate_username])

    user_state = fields.Dict(missing=lambda: {})
    state_public_keys = fields.List(fields.String(
        validate=validate.Length(min=1, max=256)),
        missing=None)

    @marshmallow.post_load(pass_original=True)
    def _add_unknown(self, data, original):
        return add_missing_fields(data, original, self.fields)


class MessageBodySchema(ChannelstreamSchema):
    timestamp = fields.DateTime(missing=lambda: datetime.utcnow().isoformat())
    user = fields.String(
        required=True,
        validate=validate.Length(min=1, max=512))
    message = fields.Dict()
    no_history = fields.Boolean(missing=False)
    pm_users = fields.List(
        fields.String(
            validate=validate.Length(min=1, max=512)),
        missing=lambda: [],
    )
    exclude_users = fields.List(fields.String(
        missing=lambda: [],
        validate=validate.Length(min=1, max=512)))
    channel = fields.String(
        validate=validate.Length(min=1, max=256))

    # @marshmallow.post_load(pass_original=True)
    # def _add_unknown(self, data, original):
    #     return add_missing_fields(data, original, self.fields)


class DisconnectBodySchema(ChannelstreamSchema):
    conn_id = fields.String(
        required=True,
        validate=[validate.Length(min=1, max=256),
                  validate_connection_id])


class ChannelConfigBodySchema(ChannelstreamSchema):

    @marshmallow.post_load(pass_original=True)
    def _add_unknown(self, data, original):
        return add_missing_fields(data, original, self.fields)


class ChannelInfoBodySchema(ChannelstreamSchema):
    @marshmallow.post_load(pass_original=True)
    def _add_unknown(self, data, original):
        return add_missing_fields(data, original, self.fields)


def add_missing_fields(data, original, fields):
    for key, val in original.items():
        if key not in fields:
            data[key] = val
    return data
